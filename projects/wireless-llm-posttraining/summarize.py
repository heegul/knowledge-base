"""Verify saved responses against the independent solver and emit compact results."""

import argparse
import hashlib
import json
from pathlib import Path

from problem import score


SETS = ("test_id", "test_rate_shift", "test_more_users")
STAGES = ("base", "sft", "grpo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    args = ap.parse_args()
    evaluations = {stage: json.loads((args.run_dir / f"eval_{stage}.json").read_text())
                   for stage in STAGES}
    table = {}
    paired = {}
    for name in SETS:
        expected_ids = None
        table[name] = {}
        for stage in STAGES:
            section = evaluations[stage]["sets"][name]
            rows = section["rows"]
            ids = [r["id"] for r in rows]
            if expected_ids is None:
                expected_ids = ids
            assert ids == expected_ids and len(ids) == len(set(ids)) == 64
            for row in rows:
                recomputed = score(row["rates"], row["response"])
                for key in ("feasible", "optimal", "achieved_rate", "optimal_rate"):
                    assert row[key] == recomputed[key], (stage, name, row["id"], key)
                assert abs(row["ratio"] - recomputed["ratio"]) < 1e-12
            table[name][stage] = {
                "n": len(rows), "feasible": sum(r["feasible"] for r in rows),
                "optimal": sum(r["optimal"] for r in rows),
                "mean_optimality_ratio": sum(r["ratio"] for r in rows) / len(rows),
            }
        before = evaluations["sft"]["sets"][name]["rows"]
        after = evaluations["grpo"]["sets"][name]["rows"]
        paired[name] = {
            "sft_wrong_grpo_right": sum(not x["optimal"] and y["optimal"] for x, y in zip(before, after)),
            "sft_right_grpo_wrong": sum(x["optimal"] and not y["optimal"] for x, y in zip(before, after)),
        }
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((args.run_dir / "data").glob("*.jsonl"))}
    output = {"table": table, "paired_sft_vs_grpo": paired, "dataset_sha256": hashes}
    (args.run_dir / "summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output["table"], indent=2))


if __name__ == "__main__":
    main()
