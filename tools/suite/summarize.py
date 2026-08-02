#!/usr/bin/env python3
import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


METRICS = [
    "cpu_util_pct",
    "cpu0_temp_c",
    "cpu1_temp_c",
    "system_power_w",
    "nvme_max_c",
    "ram_used_gib",
    "ram_available_gib",
    "swap_used_gib",
    "swap_in_mib_s",
    "swap_out_mib_s",
    "major_faults_s",
    "nvme_read_mib_s",
    "nvme_write_mib_s",
    "gpu0_power_w",
    "gpu0_temp_c",
    "gpu0_util_pct",
    "gpu0_mem_used_mib",
    "gpu0_pcie_rx_mib_s",
    "gpu0_pcie_tx_mib_s",
]


def finite(value):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except Exception:
        return None


def aggregate(rows):
    result = {}
    for metric in METRICS:
        values = [finite(row.get(metric)) for row in rows]
        values = [value for value in values if value is not None]
        if values:
            result[metric] = {
                "avg": statistics.fmean(values),
                "peak": max(values),
                "min": min(values),
            }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    results = [
        json.loads(line)
        for line in (run_dir / "results.jsonl").read_text().splitlines()
        if line.strip()
    ]
    metrics = []
    for metrics_path in sorted(run_dir.glob("metrics*.csv")):
        with metrics_path.open() as handle:
            metrics.extend(csv.DictReader(handle))
    for result in results:
        start = result["started_epoch"]
        end = result["ended_epoch"]
        rows = [
            row
            for row in metrics
            if start <= float(row["epoch"]) <= end
        ]
        result["system_metrics"] = aggregate(rows)

    grouped = defaultdict(list)
    for result in results:
        grouped[result["case_id"]].append(result)
    summary = {
        "runtime": results[0]["runtime"] if results else run_dir.name,
        "result_count": len(results),
        "pass_count": sum(bool(r.get("score", {}).get("passed")) for r in results),
        "error_count": sum(bool(r.get("error")) for r in results),
        "suite_wall_seconds": (
            max(r["ended_epoch"] for r in results)
            - min(r["started_epoch"] for r in results)
            if results
            else 0
        ),
        "overall_metrics": aggregate(metrics),
        "cases": {},
    }
    for case_id, items in sorted(grouped.items()):
        summary["cases"][case_id] = {
            "runs": len(items),
            "passes": sum(bool(item.get("score", {}).get("passed")) for item in items),
            "errors": sum(bool(item.get("error")) for item in items),
            "wall_seconds": [item["wall_seconds"] for item in items],
            "completion_tokens": [item["usage"]["completion_tokens"] for item in items],
            "effective_completion_tokens_per_second": [
                item["effective_completion_tokens_per_second"] for item in items
            ],
            "tool_calls": [
                [call["name"] for call in item["calls"]] for item in items
            ],
            "finals": [item["final"] for item in items],
            "system_metrics": [item["system_metrics"] for item in items],
        }
    (run_dir / "enriched-results.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
