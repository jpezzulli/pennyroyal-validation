#!/usr/bin/env python3
import csv
import json
import statistics
import sys
from pathlib import Path


root = Path(sys.argv[1])
results = [json.loads(line) for line in (root / "results.jsonl").read_text().splitlines() if line.strip()]
measured = [item for item in results if item.get("kind") == "measured"]
with (root / "metrics.csv").open() as handle:
    metrics = list(csv.DictReader(handle))


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def values(rows, key):
    return [value for row in rows if (value := number(row.get(key))) is not None]


def stats(rows, key):
    vals = values(rows, key)
    return {
        "avg": statistics.fmean(vals) if vals else None,
        "peak": max(vals) if vals else None,
    }


def interval_rows(item):
    return [
        row for row in metrics
        if item["started_epoch"] <= number(row.get("epoch")) <= item["ended_epoch"]
    ]


per_request = []
for item in measured:
    rows = interval_rows(item)
    host = values(rows, "system_power_w")
    gpu = values(rows, "gpu0_power_w")
    combined = [a + b for a, b in zip(host, gpu)]
    usage = item.get("usage") or {}
    api_tokens = usage.get("completion_tokens")
    per_request.append({
        "request_id": item["request_id"],
        "case_id": item["case_id"],
        "turn": item["turn"],
        "wall_seconds": item["wall_seconds"],
        "api_completion_tokens": api_tokens,
        "local_generated_tokens": item["local_generated_tokens"],
        "effective_local_tokens_per_second": (
            item["local_generated_tokens"] / item["wall_seconds"]
            if item["wall_seconds"] else None
        ),
        "finish_reason": item["finish_reason"],
        "termination": item["termination"],
        "error": item["error"],
        "loop_events": item["loop_events"],
        "host_power_w": stats(rows, "system_power_w"),
        "gpu_power_w": stats(rows, "gpu0_power_w"),
        "combined_power_w": {
            "avg": statistics.fmean(combined) if combined else None,
            "peak": max(combined) if combined else None,
        },
        "cpu0_temp_peak_c": stats(rows, "cpu0_temp_c")["peak"],
        "cpu1_temp_peak_c": stats(rows, "cpu1_temp_c")["peak"],
        "gpu_temp_peak_c": stats(rows, "gpu0_temp_c")["peak"],
        "gpu_util_pct": stats(rows, "gpu0_util_pct"),
        "ram_used_peak_gib": stats(rows, "ram_used_gib")["peak"],
        "swap_used_peak_gib": stats(rows, "swap_used_gib")["peak"],
        "swap_in_peak_mib_s": stats(rows, "swap_in_mib_s")["peak"],
        "major_faults_peak_s": stats(rows, "major_faults_s")["peak"],
        "pcie_rx_peak_mib_s": stats(rows, "gpu0_pcie_rx_mib_s")["peak"],
        "pcie_tx_peak_mib_s": stats(rows, "gpu0_pcie_tx_mib_s")["peak"],
    })

all_measured_rows = [row for item in measured for row in interval_rows(item)]
host = values(all_measured_rows, "system_power_w")
gpu = values(all_measured_rows, "gpu0_power_w")
combined = [a + b for a, b in zip(host, gpu)]
summary = {
    "request_count": len(measured),
    "total_wall_seconds": sum(item["wall_seconds"] for item in measured),
    "total_local_generated_tokens": sum(item["local_generated_tokens"] for item in measured),
    "aggregate_effective_local_tokens_per_second": (
        sum(item["local_generated_tokens"] for item in measured)
        / sum(item["wall_seconds"] for item in measured)
    ),
    "finish_reasons": {reason: sum(item["finish_reason"] == reason for item in measured) for reason in {item["finish_reason"] for item in measured}},
    "errors": sum(bool(item["error"]) for item in measured),
    "hard_loop_terminations": sum(item["termination"] == "hard_loop" for item in measured),
    "heat_terminations": sum(item["termination"] == "heat_guard" for item in measured),
    "operational_loop_events": sum(len(item["loop_events"]) for item in measured),
    "host_power_w": stats(all_measured_rows, "system_power_w"),
    "gpu_power_w": stats(all_measured_rows, "gpu0_power_w"),
    "combined_power_w": {
        "avg": statistics.fmean(combined) if combined else None,
        "peak": max(combined) if combined else None,
    },
    "cpu0_temp_peak_c": stats(all_measured_rows, "cpu0_temp_c")["peak"],
    "cpu1_temp_peak_c": stats(all_measured_rows, "cpu1_temp_c")["peak"],
    "gpu_temp_peak_c": stats(all_measured_rows, "gpu0_temp_c")["peak"],
    "gpu_util_pct": stats(all_measured_rows, "gpu0_util_pct"),
    "ram_used_peak_gib": stats(all_measured_rows, "ram_used_gib")["peak"],
    "swap_used_peak_gib": stats(all_measured_rows, "swap_used_gib")["peak"],
    "swap_in_peak_mib_s": stats(all_measured_rows, "swap_in_mib_s")["peak"],
    "major_faults_peak_s": stats(all_measured_rows, "major_faults_s")["peak"],
    "pcie_rx_peak_mib_s": stats(all_measured_rows, "gpu0_pcie_rx_mib_s")["peak"],
    "pcie_tx_peak_mib_s": stats(all_measured_rows, "gpu0_pcie_tx_mib_s")["peak"],
    "per_request": per_request,
}
(root / "operational-summary.json").write_text(json.dumps(summary, indent=2) + "\n")

with (root / "per-request-summary.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow([
        "request_id", "case_id", "turn", "wall_seconds", "local_tokens",
        "effective_tps", "finish_reason", "host_power_avg_w", "host_power_peak_w",
        "gpu_power_avg_w", "gpu_power_peak_w", "combined_power_avg_w",
        "combined_power_peak_w", "cpu_peak_c", "gpu_peak_c",
    ])
    for item in per_request:
        writer.writerow([
            item["request_id"], item["case_id"], item["turn"], item["wall_seconds"],
            item["local_generated_tokens"], item["effective_local_tokens_per_second"],
            item["finish_reason"], item["host_power_w"]["avg"],
            item["host_power_w"]["peak"], item["gpu_power_w"]["avg"],
            item["gpu_power_w"]["peak"], item["combined_power_w"]["avg"],
            item["combined_power_w"]["peak"],
            max(item["cpu0_temp_peak_c"] or 0, item["cpu1_temp_peak_c"] or 0),
            item["gpu_temp_peak_c"],
        ])
