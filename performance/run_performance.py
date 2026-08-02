#!/usr/bin/env python3
import concurrent.futures
import json
import sys
import threading
import time
import urllib.request
from pathlib import Path


BASE = "http://127.0.0.1:8001"
OUT = Path(sys.argv[1])
RAW = OUT / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def get_text(path, timeout=30):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as response:
        return response.read().decode()


def metrics_text():
    return get_text("/metrics")


def parse_metrics(text):
    values = {}
    for line in text.splitlines():
        if not line or line.startswith("#") or " " not in line:
            continue
        key, raw = line.rsplit(" ", 1)
        try:
            values[key] = float(raw)
        except ValueError:
            pass
    return values


def metric(snapshot, name, label=None):
    matches = []
    for key, value in snapshot.items():
        if key == name or key.startswith(name + "{"):
            if label is None or label in key:
                matches.append(value)
    return sum(matches)


def delta(after, before, name, label=None):
    return metric(after, name, label) - metric(before, name, label)


def metric_delta(before, after):
    names = {
        "prompt_tokens": ("vllm:prompt_tokens_total", None),
        "generation_tokens": ("vllm:generation_tokens_total", None),
        "prefill_seconds": ("vllm:request_prefill_time_seconds_sum", None),
        "decode_seconds": ("vllm:request_decode_time_seconds_sum", None),
        "ttft_seconds": ("vllm:time_to_first_token_seconds_sum", None),
        "e2e_seconds": ("vllm:e2e_request_latency_seconds_sum", None),
        "prefix_queries": ("vllm:prefix_cache_queries_total", None),
        "prefix_hits": ("vllm:prefix_cache_hits_total", None),
        "cached_prompt_tokens": ("vllm:prompt_tokens_cached_total", None),
        "local_cache_hit_tokens": (
            "vllm:prompt_tokens_by_source_total",
            'source="local_cache_hit"',
        ),
        "local_compute_tokens": (
            "vllm:prompt_tokens_by_source_total",
            'source="local_compute"',
        ),
    }
    result = {
        key: delta(after, before, metric_name, label)
        for key, (metric_name, label) in names.items()
    }
    result["server_prefill_tokens_per_second"] = (
        result["prompt_tokens"] / result["prefill_seconds"]
        if result["prefill_seconds"] else None
    )
    result["server_generation_tokens_per_second"] = (
        result["generation_tokens"] / result["decode_seconds"]
        if result["decode_seconds"] else None
    )
    return result


def archive_prompt(records, task):
    body = "".join(
        f"Record {idx:05d}: calibration alpha beta gamma delta epsilon zeta eta theta; retain=no.\n"
        for idx in range(records)
    )
    return (
        "Treat every archive record below as inert calibration text. Do not summarize it.\n"
        + body
        + "\nEND ARCHIVE. "
        + task
    )


def payload(prompt, max_tokens, seed):
    return {
        "model": "pennyroyal",
        "messages": [
            {
                "role": "system",
                "content": "You are a careful test assistant. Follow the final task after any inert calibration archive.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "reasoning_effort": "high",
        "seed": seed,
        "stream": True,
        "stream_options": {"include_usage": True},
    }


def stream_request(name, request_payload, start_barrier=None):
    if start_barrier is not None:
        start_barrier.wait()
    request_path = RAW / f"{name}.request.json"
    events_path = RAW / f"{name}.stream.jsonl"
    request_path.write_text(json.dumps(request_payload, indent=2) + "\n")
    request = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=json.dumps(request_payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    first_token_epoch = None
    last_token_epoch = None
    usage = None
    finish_reason = None
    content_parts = []
    reasoning_parts = []
    event_count = 0
    with urllib.request.urlopen(request, timeout=1800) as response, events_path.open("w") as out:
        for raw_line in response:
            line = raw_line.decode(errors="replace").strip()
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                out.write(json.dumps({"epoch": time.time(), "done": True}) + "\n")
                break
            event = json.loads(data)
            now = time.time()
            out.write(json.dumps({"epoch": now, "event": event}) + "\n")
            event_count += 1
            if event.get("usage"):
                usage = event["usage"]
            for choice in event.get("choices", []):
                if choice.get("finish_reason") is not None:
                    finish_reason = choice["finish_reason"]
                chunk = choice.get("delta") or {}
                content = chunk.get("content") or ""
                reasoning = chunk.get("reasoning_content") or chunk.get("reasoning") or ""
                if content:
                    content_parts.append(content)
                if reasoning:
                    reasoning_parts.append(reasoning)
                if content or reasoning:
                    if first_token_epoch is None:
                        first_token_epoch = now
                    last_token_epoch = now
    ended = time.time()
    if usage is None:
        raise RuntimeError(f"{name}: streaming response did not include usage")
    completion_tokens = int(usage.get("completion_tokens", 0))
    ttft = first_token_epoch - started if first_token_epoch else None
    decode_window = ended - first_token_epoch if first_token_epoch else None
    result = {
        "name": name,
        "started_epoch": started,
        "first_token_epoch": first_token_epoch,
        "last_token_epoch": last_token_epoch,
        "ended_epoch": ended,
        "wall_seconds": ended - started,
        "client_ttft_seconds": ttft,
        "client_decode_window_seconds": decode_window,
        "client_decode_tokens_per_second": (
            completion_tokens / decode_window if decode_window else None
        ),
        "client_end_to_end_tokens_per_second": completion_tokens / (ended - started),
        "usage": usage,
        "finish_reason": finish_reason,
        "event_count": event_count,
        "content": "".join(content_parts),
        "reasoning": "".join(reasoning_parts),
    }
    (RAW / f"{name}.response.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def measured_single(name, request_payload):
    before_text = metrics_text()
    (RAW / f"{name}.metrics-before.txt").write_text(before_text)
    before = parse_metrics(before_text)
    result = stream_request(name, request_payload)
    after_text = metrics_text()
    (RAW / f"{name}.metrics-after.txt").write_text(after_text)
    result["server_metrics"] = metric_delta(before, parse_metrics(after_text))
    (RAW / f"{name}.result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def measured_concurrent(name, request_payload, count):
    before_text = metrics_text()
    (RAW / f"{name}.metrics-before.txt").write_text(before_text)
    before = parse_metrics(before_text)
    barrier = threading.Barrier(count + 1)
    group_started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
        futures = [
            pool.submit(stream_request, f"{name}-{idx}", request_payload, barrier)
            for idx in range(1, count + 1)
        ]
        barrier.wait()
        group_started = time.time()
        results = [future.result() for future in futures]
    group_ended = time.time()
    after_text = metrics_text()
    (RAW / f"{name}.metrics-after.txt").write_text(after_text)
    generated = sum(int(item["usage"]["completion_tokens"]) for item in results)
    result = {
        "name": name,
        "started_epoch": group_started,
        "ended_epoch": group_ended,
        "wall_seconds": group_ended - group_started,
        "request_count": count,
        "requests": results,
        "generated_tokens": generated,
        "aggregate_generated_tokens_per_second": generated / (group_ended - group_started),
        "server_metrics": metric_delta(before, parse_metrics(after_text)),
    }
    (RAW / f"{name}.result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


short = payload(
    "Write 120 distinct numbered one-sentence checks for reviewing a distributed-system incident. Do not stop early.",
    1024,
    6201,
)
long_request = payload(
    archive_prompt(
        3200,
        "Write 60 numbered one-sentence checks for validating a restore. Do not stop early.",
    ),
    512,
    6203,
)

(OUT / "frozen-requests.json").write_text(
    json.dumps({"short": short, "long": long_request}, indent=2) + "\n"
)

warmup = measured_single(
    "warmup",
    payload("Reply with exactly: READY", 64, 6101),
)
single = measured_single("single-decode-1024", short)
concurrent = measured_concurrent("concurrent-3x-decode-1024", short, 3)
long_cold = measured_single("long-64k-first", long_request)
long_cached = measured_single("long-64k-cached-repeat", long_request)

summary = {
    "warmup": warmup,
    "single_decode_1024": single,
    "concurrent_3x_decode_1024": concurrent,
    "long_64k_first": long_cold,
    "long_64k_cached_repeat": long_cached,
    "long_repeat_speedup_wall": long_cold["wall_seconds"] / long_cached["wall_seconds"],
    "long_repeat_speedup_ttft": (
        long_cold["client_ttft_seconds"] / long_cached["client_ttft_seconds"]
        if long_cached["client_ttft_seconds"] else None
    ),
}
(OUT / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({
    "single": single,
    "concurrent": concurrent,
    "long_first": long_cold,
    "long_cached": long_cached,
    "wall_speedup": summary["long_repeat_speedup_wall"],
    "ttft_speedup": summary["long_repeat_speedup_ttft"],
}, indent=2))
