"""Summarize native mLibraryLoadBench JSON receipts without discarding samples."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    value = data.get("value", data)
    report = value.get("Server", value)
    groups = defaultdict(list)
    for sample in report["Samples"]:
        groups[sample["Name"]].append(sample)
    result = {}
    for name, samples in sorted(groups.items()):
        elapsed = [sample["ElapsedMs"] for sample in samples]
        per_iteration = [sample["ElapsedMs"] / sample["Iterations"] for sample in samples]
        per_operation = [sample["ElapsedMs"] / sample["Operations"] for sample in samples]
        result[name] = {
            "Unit": samples[0]["Unit"],
            "Samples": len(samples),
            "Iterations": sorted({sample["Iterations"] for sample in samples}),
            "Operations": sorted({sample["Operations"] for sample in samples}),
            "AllVerified": all(sample["Verified"] for sample in samples),
            "BelowTarget": sum(value < report["TargetMs"] for value in elapsed),
            "BatchMs": {"Median": statistics.median(elapsed), "Min": min(elapsed), "Max": max(elapsed)},
            "MsPerIteration": {"Median": statistics.median(per_iteration), "Min": min(per_iteration), "Max": max(per_iteration)},
            "MsPerOperation": {"Median": statistics.median(per_operation), "Min": min(per_operation), "Max": max(per_operation)},
        }
    return {
        "Source": str(path.resolve()),
        "Clock": report["Clock"],
        "ClockMinimumPositiveMs": report["ClockMinimumPositiveMs"],
        "ElapsedSeconds": report["End"] - report["Start"],
        "Trials": report["Trials"],
        "TargetMs": report["TargetMs"],
        "Failures": report["Failures"],
        "Truncated": report["Truncated"],
        "Cases": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path, nargs="?")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    before = load(args.before)
    summary = {"Before": before}
    if args.after:
        after = load(args.after)
        summary["After"] = after
        comparisons = {}
        for name in sorted(before["Cases"].keys() & after["Cases"].keys()):
            base = before["Cases"][name]
            candidate = after["Cases"][name]
            denominator = base["MsPerIteration"]["Median"]
            delta = candidate["MsPerIteration"]["Median"] - denominator
            comparisons[name] = {
                "UnitMatches": base["Unit"] == candidate["Unit"],
                "BeforeMedianMs": denominator,
                "AfterMedianMs": candidate["MsPerIteration"]["Median"],
                "DeltaMedianMs": delta,
                "DeltaPercent": None if denominator == 0 else delta * 100 / denominator,
                "RangesOverlap": base["MsPerIteration"]["Min"] <= candidate["MsPerIteration"]["Max"] and candidate["MsPerIteration"]["Min"] <= base["MsPerIteration"]["Max"],
            }
        summary["Comparison"] = comparisons
        summary["Interpretation"] = "Observed elapsed-time comparison. A median difference alone does not establish causality or statistical significance."
    output = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
