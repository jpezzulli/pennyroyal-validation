#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path


STOP = False


def stop_handler(_signum, _frame):
    global STOP
    STOP = True


def command(args):
    try:
        return subprocess.check_output(
            args, stderr=subprocess.DEVNULL, text=True, timeout=3
        )
    except Exception:
        return ""


def number(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


def sensors_values():
    raw = command(["sensors", "-j"])
    values = {
        "cpu0_temp_c": None,
        "cpu1_temp_c": None,
        "system_power_w": None,
        "nvme_max_c": None,
    }
    if not raw:
        return values
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return values
    nvme = []
    for chip, sections in data.items():
        if chip.startswith("coretemp-isa-"):
            package = sections.get("Package id 0") or sections.get("Package id 1") or {}
            temp = next(
                (number(v) for k, v in package.items() if k.endswith("_input")), None
            )
            if chip.endswith("0000"):
                values["cpu0_temp_c"] = temp
            elif chip.endswith("0001"):
                values["cpu1_temp_c"] = temp
        elif chip.startswith("power_meter-"):
            section = sections.get("power1", {})
            values["system_power_w"] = next(
                (
                    number(v)
                    for k, v in section.items()
                    if k.endswith("_input") or k.endswith("_average")
                ),
                None,
            )
        elif chip.startswith("nvme-"):
            for section_name, section in sections.items():
                if section_name == "Sensor 3":
                    continue
                if section_name not in {"Composite", "Sensor 1", "Sensor 2"}:
                    continue
                for key, value in section.items():
                    if key.endswith("_input"):
                        parsed = number(value)
                        if parsed is not None:
                            nvme.append(parsed)
    values["nvme_max_c"] = max(nvme) if nvme else None
    return values


def gpu_values():
    raw = command(
        [
            "nvidia-smi",
            "--query-gpu=index,power.draw,power.limit,temperature.gpu,"
            "utilization.gpu,utilization.memory,memory.used,memory.total,"
            "clocks.sm,clocks.mem",
            "--format=csv,noheader,nounits",
        ]
    )
    result = {}
    for line in raw.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 10:
            continue
        idx = int(parts[0])
        result[idx] = {
            "power_w": number(parts[1]),
            "power_limit_w": number(parts[2]),
            "temp_c": number(parts[3]),
            "util_pct": number(parts[4]),
            "mem_util_pct": number(parts[5]),
            "mem_used_mib": number(parts[6]),
            "mem_total_mib": number(parts[7]),
            "sm_clock_mhz": number(parts[8]),
            "mem_clock_mhz": number(parts[9]),
        }
    dmon = command(["nvidia-smi", "dmon", "-s", "t", "-c", "1"])
    rows = [
        line.split()
        for line in dmon.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for row in rows:
        if len(row) >= 3 and row[0].isdigit():
            idx = int(row[0])
            result.setdefault(idx, {})
            result[idx]["pcie_rx_mib_s"] = number(row[-2])
            result[idx]["pcie_tx_mib_s"] = number(row[-1])
    return result


def mem_values():
    values = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0])
    except Exception:
        pass
    return {
        "ram_used_gib": (
            (values.get("MemTotal", 0) - values.get("MemAvailable", 0))
            / 1024
            / 1024
        ),
        "ram_available_gib": values.get("MemAvailable", 0) / 1024 / 1024,
        "swap_used_gib": (
            (values.get("SwapTotal", 0) - values.get("SwapFree", 0))
            / 1024
            / 1024
        ),
        "swap_free_gib": values.get("SwapFree", 0) / 1024 / 1024,
    }


def cpu_counters():
    fields = Path("/proc/stat").read_text().splitlines()[0].split()[1:]
    nums = [int(v) for v in fields]
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
    return sum(nums), idle


def vm_counters():
    result = {"pswpin": 0, "pswpout": 0, "pgmajfault": 0}
    for line in Path("/proc/vmstat").read_text().splitlines():
        key, value = line.split()
        if key in result:
            result[key] = int(value)
    return result


def disk_counters():
    read_sectors = 0
    write_sectors = 0
    for line in Path("/proc/diskstats").read_text().splitlines():
        fields = line.split()
        if len(fields) < 14 or not re.fullmatch(r"nvme\d+n\d+", fields[2]):
            continue
        read_sectors += int(fields[5])
        write_sectors += int(fields[9])
    return read_sectors, write_sectors


FIELDS = [
    "timestamp",
    "epoch",
    "cpu_util_pct",
    "load1",
    "cpu0_temp_c",
    "cpu1_temp_c",
    "system_power_w",
    "nvme_max_c",
    "ram_used_gib",
    "ram_available_gib",
    "swap_used_gib",
    "swap_free_gib",
    "swap_in_mib_s",
    "swap_out_mib_s",
    "major_faults_s",
    "nvme_read_mib_s",
    "nvme_write_mib_s",
    "gpu0_power_w",
    "gpu0_power_limit_w",
    "gpu0_temp_c",
    "gpu0_util_pct",
    "gpu0_mem_util_pct",
    "gpu0_mem_used_mib",
    "gpu0_mem_total_mib",
    "gpu0_sm_clock_mhz",
    "gpu0_mem_clock_mhz",
    "gpu0_pcie_rx_mib_s",
    "gpu0_pcie_tx_mib_s",
    "gpu1_power_w",
    "gpu1_temp_c",
    "gpu1_util_pct",
    "gpu1_mem_used_mib",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)

    prev_time = time.time()
    prev_cpu = cpu_counters()
    prev_vm = vm_counters()
    prev_disk = disk_counters()

    with open(args.output, "w", newline="", buffering=1) as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        while not STOP:
            started = time.time()
            sensors = sensors_values()
            gpus = gpu_values()
            mem = mem_values()
            current_cpu = cpu_counters()
            current_vm = vm_counters()
            current_disk = disk_counters()
            elapsed = max(started - prev_time, 0.001)
            total_delta = current_cpu[0] - prev_cpu[0]
            idle_delta = current_cpu[1] - prev_cpu[1]
            cpu_util = (
                100.0 * (total_delta - idle_delta) / total_delta
                if total_delta > 0
                else 0.0
            )
            gpu0 = gpus.get(0, {})
            gpu1 = gpus.get(1, {})
            row = {
                "timestamp": time.strftime(
                    "%Y-%m-%dT%H:%M:%S%z", time.localtime(started)
                ),
                "epoch": f"{started:.6f}",
                "cpu_util_pct": f"{cpu_util:.3f}",
                "load1": f"{os.getloadavg()[0]:.3f}",
                **sensors,
                **mem,
                "swap_in_mib_s": (current_vm["pswpin"] - prev_vm["pswpin"])
                * 4
                / 1024
                / elapsed,
                "swap_out_mib_s": (current_vm["pswpout"] - prev_vm["pswpout"])
                * 4
                / 1024
                / elapsed,
                "major_faults_s": (
                    current_vm["pgmajfault"] - prev_vm["pgmajfault"]
                )
                / elapsed,
                "nvme_read_mib_s": (current_disk[0] - prev_disk[0])
                * 512
                / 1024
                / 1024
                / elapsed,
                "nvme_write_mib_s": (current_disk[1] - prev_disk[1])
                * 512
                / 1024
                / 1024
                / elapsed,
                "gpu0_power_w": gpu0.get("power_w"),
                "gpu0_power_limit_w": gpu0.get("power_limit_w"),
                "gpu0_temp_c": gpu0.get("temp_c"),
                "gpu0_util_pct": gpu0.get("util_pct"),
                "gpu0_mem_util_pct": gpu0.get("mem_util_pct"),
                "gpu0_mem_used_mib": gpu0.get("mem_used_mib"),
                "gpu0_mem_total_mib": gpu0.get("mem_total_mib"),
                "gpu0_sm_clock_mhz": gpu0.get("sm_clock_mhz"),
                "gpu0_mem_clock_mhz": gpu0.get("mem_clock_mhz"),
                "gpu0_pcie_rx_mib_s": gpu0.get("pcie_rx_mib_s"),
                "gpu0_pcie_tx_mib_s": gpu0.get("pcie_tx_mib_s"),
                "gpu1_power_w": gpu1.get("power_w"),
                "gpu1_temp_c": gpu1.get("temp_c"),
                "gpu1_util_pct": gpu1.get("util_pct"),
                "gpu1_mem_used_mib": gpu1.get("mem_used_mib"),
            }
            writer.writerow(row)
            prev_time = started
            prev_cpu = current_cpu
            prev_vm = current_vm
            prev_disk = current_disk
            delay = args.interval - (time.time() - started)
            if delay > 0:
                time.sleep(delay)


if __name__ == "__main__":
    main()
