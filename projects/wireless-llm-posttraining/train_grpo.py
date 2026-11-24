"""Solver-reward adaptation of DeepSeekMath outcome-supervision GRPO (Eq. 3-4).

This preserves group-normalized advantages, token-level clipped ratios, and
the reference-policy KL estimator.  The reward is computed by an independent
exact solver for a tiny wireless scheduling task, as requested by the user.
It is not a reproduction of DeepSeekMath's learned-reward math experiment.
"""

import argparse
import json
import random
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from problem import DATA_SEED, prompt, score, write_splits


def rollout(model, tokenizer, rates, group_size, max_new_tokens):
    prefix = tokenizer(prompt(rates), return_tensors="pt").to("cuda")
    p = prefix.input_ids.shape[1]
    model.eval()
    with torch.inference_mode():
        generated = model.generate(**prefix, do_sample=True, temperature=1.0,
                                   top_p=1.0, num_return_sequences=group_size,
                                   max_new_tokens=max_new_tokens,
                                   pad_token_id=tokenizer.eos_token_id)
    completions = []
    responses = []
    for row in generated:
        ids = row[p:].tolist()
        if tokenizer.eos_token_id in ids:
            ids = ids[:ids.index(tokenizer.eos_token_id) + 1]
        completions.append(ids)
        responses.append(tokenizer.decode(ids, skip_special_tokens=True))
    return prefix.input_ids[0].tolist(), completions, responses


def prepare_group(prefix, completions, pad_token, device):
    max_len = max(map(len, completions))
    total = len(prefix) + max_len
    ids = torch.full((len(completions), total), pad_token, dtype=torch.long, device=device)
    attention = torch.zeros_like(ids)
    targets = torch.full((len(completions), max_len), pad_token, dtype=torch.long, device=device)
    mask = torch.zeros((len(completions), max_len), dtype=torch.float32, device=device)
    for i, completion in enumerate(completions):
        n = len(completion)
        ids[i, :len(prefix)] = torch.tensor(prefix, device=device)
        ids[i, len(prefix):len(prefix) + n] = torch.tensor(completion, device=device)
        attention[i, :len(prefix) + n] = 1
        targets[i, :n] = torch.tensor(completion, device=device)
        mask[i, :n] = 1
    return {"input_ids": ids, "attention_mask": attention}, targets, mask, len(prefix)


def token_log_probs(model, inputs, targets, prefix_len):
    logits = model(**inputs).logits
    generated_logits = logits[:, prefix_len - 1:prefix_len + targets.shape[1] - 1].float()
    return generated_logits.log_softmax(dim=-1).gather(-1, targets.unsqueeze(-1)).squeeze(-1)


def grpo_loss(current, old, reference, mask, advantages, epsilon, beta):
    """Negative of Eq. 3: average tokens within completion, then completions."""
    ratio = (current - old).exp()
    clipped = ratio.clamp(1 - epsilon, 1 + epsilon)
    surrogate = torch.minimum(ratio * advantages[:, None], clipped * advantages[:, None])
    log_ref_over_policy = reference - current
    kl = log_ref_over_policy.exp() - log_ref_over_policy - 1
    per_completion = ((surrogate - beta * kl) * mask).sum(1) / mask.sum(1)
    return -per_completion.mean(), float((kl.detach() * mask).sum() / mask.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--groups", type=int, default=120)
    ap.add_argument("--group-size", type=int, default=4)
    ap.add_argument("--mu", type=int, default=2)
    ap.add_argument("--epsilon", type=float, default=0.2)
    ap.add_argument("--beta", type=float, default=0.04)
    ap.add_argument("--lr", type=float, default=1e-5)
    ap.add_argument("--max-new-tokens", type=int, default=20)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    if args.group_size < 2 or args.mu < 1:
        raise ValueError("Need >=2 samples per group and >=1 policy iteration")
    torch.manual_seed(DATA_SEED + 2)
    rng = random.Random(DATA_SEED + 2)
    splits = write_splits(args.run_dir / "data")
    sft_dir = args.run_dir / "checkpoints" / "sft"
    tokenizer = AutoTokenizer.from_pretrained(sft_dir, local_files_only=True)
    policy = AutoModelForCausalLM.from_pretrained(sft_dir, local_files_only=True,
                                                 dtype=torch.float32).to("cuda")
    reference = AutoModelForCausalLM.from_pretrained(sft_dir, local_files_only=True,
                                                    dtype=torch.float32).to("cuda")
    policy.config.use_cache = False
    reference.eval()
    for parameter in reference.parameters():
        parameter.requires_grad_(False)
    optimizer = torch.optim.AdamW(policy.parameters(), lr=args.lr, weight_decay=0.0)
    prompts = splits["rl_prompts"].copy()
    rng.shuffle(prompts)
    n_groups = 1 if args.smoke else args.groups
    logs = []
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for step in range(n_groups):
        item = prompts[step % len(prompts)]
        prefix, completions, responses = rollout(policy, tokenizer, item["rates"],
                                                   args.group_size, args.max_new_tokens)
        rewards = torch.tensor([score(item["rates"], x)["reward"] for x in responses],
                               dtype=torch.float32, device="cuda")
        inputs, targets, mask, prefix_len = prepare_group(prefix, completions,
                                                          tokenizer.eos_token_id, "cuda")
        policy.eval()
        with torch.inference_mode():
            old = token_log_probs(policy, inputs, targets, prefix_len).detach()
            ref = token_log_probs(reference, inputs, targets, prefix_len).detach()
        # Population standard deviation: the paper specifies group std without a
        # degrees-of-freedom convention. Equal-reward groups contain no signal.
        std = rewards.std(unbiased=False)
        entry = {"group": step + 1, "prompt_id": item["id"],
                 "rewards": [round(float(x), 4) for x in rewards],
                 "responses": responses, "reward_std": float(std),
                 "updates": 0, "losses": [], "kl": []}
        if float(std) > 0:
            advantages = (rewards - rewards.mean()) / std
            for _ in range(args.mu):
                policy.train()
                optimizer.zero_grad(set_to_none=True)
                current = token_log_probs(policy, inputs, targets, prefix_len)
                loss, kl = grpo_loss(current, old, ref, mask, advantages,
                                     args.epsilon, args.beta)
                if not torch.isfinite(loss):
                    raise RuntimeError(f"Non-finite GRPO loss at group {step + 1}")
                loss.backward()
                grad_norm = float(torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0))
                optimizer.step()
                entry["updates"] += 1
                entry["losses"].append(float(loss.detach()))
                entry["kl"].append(kl)
                entry["last_grad_norm"] = grad_norm
        entry["seconds"] = round(time.monotonic() - started, 1)
        logs.append(entry)
        if step == 0 or (step + 1) % 10 == 0:
            print(json.dumps({k: entry[k] for k in ("group", "rewards", "updates", "losses", "seconds")}),
                  flush=True)
    if not args.smoke:
        checkpoint = args.run_dir / "checkpoints" / "grpo"
        checkpoint.mkdir(parents=True, exist_ok=True)
        policy.save_pretrained(checkpoint, safe_serialization=True)
        tokenizer.save_pretrained(checkpoint)
    report = {"method": "solver-reward GRPO adaptation of DeepSeekMath Eq. 3-4",
              "source": "https://arxiv.org/html/2402.03300v3", "seed": DATA_SEED + 2,
              "group_size": args.group_size, "mu": args.mu, "epsilon": args.epsilon,
              "beta": args.beta, "learning_rate": args.lr,
              "max_new_tokens": args.max_new_tokens, "groups": n_groups,
              "total_policy_updates": sum(x["updates"] for x in logs),
              "zero_variance_groups": sum(x["reward_std"] == 0 for x in logs),
              "training_seconds": round(time.monotonic() - started, 1),
              "peak_torch_allocated_mib": round(torch.cuda.max_memory_allocated() / 2**20),
              "log": logs}
    name = "grpo_smoke.json" if args.smoke else "grpo_train.json"
    (args.run_dir / name).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"GRPO complete: {report['total_policy_updates']} policy updates", flush=True)


if __name__ == "__main__":
    main()
