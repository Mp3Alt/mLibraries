"""Summarize bounded native mNet load receipts, separating probes and load."""

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def numbers(values):
    ordered = sorted(values)
    if not ordered:
        return None
    return {
        "Count": len(ordered),
        "Min": ordered[0],
        "Median": statistics.median(ordered),
        "P95NearestRank": ordered[math.ceil(len(ordered) * 0.95) - 1],
        "Max": ordered[-1],
    }


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("receipt", type=Path)
parser.add_argument("--out", type=Path)
args = parser.parse_args()
source = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
report = source.get("value", source)
samples = report["Samples"]
groups = defaultdict(list)
for sample in samples:
    groups[sample["Name"]].append(sample)
result = {
    "Source": str(args.receipt.resolve()),
    "ReceiptVersion": source.get("version"),
    "Scope": report["Scope"],
    "ElapsedSeconds": report["FinishedAt"] - report["StartedAt"],
    "Samples": len(samples),
    "FailedClientSamples": [sample for sample in samples if sample["Status"] != "complete"],
    "ServerFailures": report["Failures"],
    "ServerCounters": {key: report[key] for key in ("Authorized", "Executed", "Denied", "InvalidDecodes", "DeniedValidation", "DeniedRun", "ThrottleRun", "Counters")},
    "ClientTotals": {key: sum(sample[key] for sample in samples) for key in ("Sent", "Ok", "Denied", "Invalid", "TimedOut", "Other")},
    "Phases": {},
    "Interpretation": "Paced one-server/two-local-client workload, not maximum throughput, WAN latency, bandwidth or cross-server certification. Expected throttle timeouts are not authorization-denial proof.",
}
for name, rows in sorted(groups.items()):
    active = [row for row in rows if row["Sent"] > 0]
    latency = [value for row in active for value in row["Latencies"]]
    phase = {
        "Samples": len(rows),
        "ActiveSamples": len(active),
        "Totals": {key: sum(row[key] for row in rows) for key in ("Sent", "Ok", "Denied", "Invalid", "TimedOut", "Other")},
        "MaximumPending": max(row["PendingMaximum"] for row in rows),
        "LatencyMs": numbers(latency),
    }
    if name.startswith("echo"):
        phase["ElapsedMsPerActiveSender"] = numbers([row["ElapsedMs"] for row in active])
        phase["ObservedRequestsPerSecondPerActiveSender"] = numbers([row["Sent"] * 1000 / row["ElapsedMs"] for row in active])
    result["Phases"][name] = phase
output = json.dumps(result, indent=2) + "\n"
if args.out:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8")
else:
    print(output, end="")
