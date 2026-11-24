"""Full-parameter, response-token supervised fine-tuning for the toy scheduler."""

import argparse
import json
import random
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from problem import DATA_SEED, format_answer, prompt, write_splits


def encode(tokenizer, item):
    prefix = tokenizer(prompt(item["rates"]), add_special_tokens=False).input_ids
    completion = tokenizer(" " + item["answer"], add_special_tokens=False).input_ids
    completion.append(tokenizer.eos_token_id)
    return prefix + completion, [-100] * len(prefix) + completion


def collate(tokenizer, rows, device):
    examples = [encode(tokenizer, row) for row in rows]
    length = max(len(ids) for ids, _ in examples)
    ids = torch.full((len(rows), length), tokenizer.eos_token_id, dtype=torch.long)
    labels = torch.full_like(ids, -100)
    mask = torch.zeros_like(ids)
    for i, (input_ids, targets) in enumerate(examples):
        n = len(input_ids)
        ids[i, :n] = torch.tensor(input_ids)
        labels[i, :n] = torch.tensor(targets)
        mask[i, :n] = 1
    return {"input_ids": ids.to(device), "labels": labels.to(device), "attention_mask": mask.to(device)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    torch.manual_seed(DATA_SEED)
    random.seed(DATA_SEED)
    splits = write_splits(args.run_dir / "data")
    tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(args.model_dir, local_files_only=True,
                                                dtype=torch.float32).to("cuda")
    model.config.use_cache = False
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
    rng = random.Random(DATA_SEED + 1)
    logs = []
    start = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for epoch in range(args.epochs):
        order = splits["train"].copy()
        rng.shuffle(order)
        model.train()
        for offset in range(0, len(order), args.batch_size):
            batch = collate(tokenizer, order[offset:offset + args.batch_size], "cuda")
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch).loss
            if not torch.isfinite(loss):
                raise RuntimeError("Non-finite SFT loss")
            loss.backward()
            grad_norm = float(torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0))
            optimizer.step()
            entry = {"step": len(logs) + 1, "epoch": epoch + 1,
                     "loss": float(loss.detach()), "grad_norm": grad_norm,
                     "seconds": round(time.monotonic() - start, 1)}
            logs.append(entry)
            if len(logs) == 1 or len(logs) % 25 == 0:
                print(json.dumps(entry), flush=True)
            if args.smoke:
                break
        if args.smoke:
            break
    if not args.smoke:
        checkpoint = args.run_dir / "checkpoints" / "sft"
        checkpoint.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(checkpoint, safe_serialization=True)
        tokenizer.save_pretrained(checkpoint)
    metadata = {"method": "full-parameter response-only SFT", "model": "HuggingFaceTB/SmolLM2-135M",
                "seed": DATA_SEED, "epochs": args.epochs, "batch_size": args.batch_size,
                "learning_rate": args.lr, "parameter_count": sum(p.numel() for p in model.parameters()),
                "updates": len(logs), "training_seconds": round(time.monotonic() - start, 1),
                "peak_torch_allocated_mib": round(torch.cuda.max_memory_allocated() / 2**20),
                "log": logs}
    (args.run_dir / ("sft_smoke.json" if args.smoke else "sft_train.json")).write_text(
        json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"SFT complete: {len(logs)} updates", flush=True)


if __name__ == "__main__":
    main()
