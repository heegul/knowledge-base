"""Copy reproducible synthetic results without machine-specific local paths."""

import argparse
import json
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_out = args.output_dir / "data"
    data_out.mkdir(exist_ok=True)
    for file in (args.run_dir / "data").glob("*.jsonl"):
        shutil.copy2(file, data_out / file.name)
    for name in ("sft_train.json", "grpo_train.json", "summary.json"):
        shutil.copy2(args.run_dir / name, args.output_dir / name)
    public_checkpoints = {"base": "HuggingFaceTB/SmolLM2-135M@93efa2f",
                          "sft": "runs/run_001/checkpoints/sft",
                          "grpo": "runs/run_001/checkpoints/grpo"}
    for stage, public_path in public_checkpoints.items():
        source = args.run_dir / f"eval_{stage}.json"
        result = json.loads(source.read_text(encoding="utf-8"))
        result["checkpoint"] = public_path
        (args.output_dir / source.name).write_text(json.dumps(result, indent=2), encoding="utf-8")
    for file in args.output_dir.rglob("*.json"):
        text = file.read_text(encoding="utf-8")
        if "C:\\Users\\" in text or "AppData" in text or "dankook" in text:
            raise RuntimeError(f"Machine-specific path found in {file}")


if __name__ == "__main__":
    main()
