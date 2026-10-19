#!/usr/bin/env python
"""Run the synthetic-data ranking evaluation and write JSON + Markdown reports.

Usage (from the backend/ directory):
    python scripts/evaluate.py                       # defaults: seed 42, 8 generated candidates/family
    python scripts/evaluate.py --seed 7 --per-family 12
    python scripts/evaluate.py --per-family 0        # hand-written seed candidates only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evaluation.runner import run_evaluation, to_markdown  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--per-family", type=int, default=8, help="generated synthetic candidates per role family")
    parser.add_argument("--bootstrap", type=int, default=1000, help="bootstrap resamples for confidence intervals")
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent.parent / "reports")
    args = parser.parse_args()

    results = run_evaluation(seed=args.seed, generated_per_family=args.per_family, n_boot=args.bootstrap)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "evaluation_results.json").write_text(json.dumps(results, indent=2))
    markdown = to_markdown(results)
    (args.out_dir / "evaluation_report.md").write_text(markdown)
    print(markdown)
    print(f"Wrote {args.out_dir / 'evaluation_results.json'} and evaluation_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
