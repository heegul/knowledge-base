"""Greedy, solver-checked evaluation shared by base, SFT, and GRPO stages."""

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from problem import prompt, score, write_splits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--stage", choices=["base", "sft", "grpo"], required=True)
    ap.add_argument("--max-new-tokens", type=int, default=32)
    args = ap.parse_args()
    splits = write_splits(args.run_dir / "data")
    tok = AutoTokenizer.from_pretrained(args.checkpoint, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(args.checkpoint, local_files_only=True,
                                                dtype=torch.float32).to("cuda")
    model.eval()
    result = {"stage": args.stage, "checkpoint": str(args.checkpoint),
              "decoding": {"method": "greedy", "max_new_tokens": args.max_new_tokens},
              "sets": {}}
    started = time.monotonic()
    for name in ("test_id", "test_rate_shift", "test_more_users"):
        rows = []
        for item in splits[name]:
            inputs = tok(prompt(item["rates"]), return_tensors="pt").to("cuda")
            with torch.inference_mode():
                generated = model.generate(**inputs, do_sample=False,
                                           max_new_tokens=args.max_new_tokens,
                                           pad_token_id=tok.eos_token_id)
            response = tok.decode(generated[0, inputs.input_ids.shape[1]:], skip_special_tokens=True)
            metrics = score(item["rates"], response)
            rows.append({"id": item["id"], "rates": item["rates"], "response": response, **metrics})
        aggregate = {"n": len(rows), "feasible_rate": sum(x["feasible"] for x in rows) / len(rows),
                     "optimal_rate": sum(x["optimal"] for x in rows) / len(rows),
                     "mean_optimality_ratio": sum(x["ratio"] for x in rows) / len(rows),
                     "rows": rows}
        result["sets"][name] = aggregate
        print(f"{args.stage} {name}: feasible={aggregate['feasible_rate']:.3f}, "
              f"optimal={aggregate['optimal_rate']:.3f}, "
              f"mean ratio={aggregate['mean_optimality_ratio']:.3f}", flush=True)
    result["evaluation_seconds"] = round(time.monotonic() - started, 1)
    (args.run_dir / f"eval_{args.stage}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
