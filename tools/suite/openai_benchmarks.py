#!/usr/bin/env python3
"""Reusable OpenAI chat-completions prefill and decode benchmarks."""

import argparse
import concurrent.futures
import hashlib
import json
import re
import threading
import time
import urllib.request
from pathlib import Path

from transformers import AutoTokenizer


TESTS = ("prefill-64k", "prefill-490k-needle", "decode-1x", "decode-4x")


def metrics_text(base):
    try:
        with urllib.request.urlopen(base + "/metrics", timeout=5) as response:
            return response.read().decode(errors="replace")
    except Exception:
        return ""


def metric_value(text, name):
    pattern = re.compile(
        rf"^{re.escape(name)}(?:\{{[^\n]*\}})? ([0-9.eE+-]+)$", re.M
    )
    values = [float(match.group(1)) for match in pattern.finditer(text)]
    return sum(values) if values else None


def sample_metrics(base, stop, samples):
    while not stop.is_set():
        text = metrics_text(base)
        samples.append(
            {
                "epoch": time.time(),
                "running": metric_value(text, "vllm:num_requests_running"),
                "waiting": metric_value(text, "vllm:num_requests_waiting"),
                "kv_usage": metric_value(text, "vllm:kv_cache_usage_perc"),
                "generation_tokens_total": metric_value(
                    text, "vllm:generation_tokens_total"
                ),
            }
        )
        stop.wait(0.25)


def request_payload(args, messages, seed):
    return {
        "model": args.model,
        "messages": messages,
        "reasoning_effort": args.reasoning_effort,
        "temperature": 1.0,
        "top_p": 0.95,
        "seed": seed,
        "max_tokens": args.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {
            "enable_thinking": True,
            "preserve_thinking": True,
            "reasoning_effort": args.reasoning_effort,
        },
    }


def stream_chat(args, payload, raw_path):
    request = urllib.request.Request(
        args.base + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )
    started_epoch = time.time()
    started_mono = time.monotonic()
    first_token_epoch = None
    first_token_mono = None
    first_reasoning_mono = None
    first_content_mono = None
    last_token_epoch = None
    reasoning = []
    content = []
    usage = None
    finish_reason = None
    status = None
    with urllib.request.urlopen(request, timeout=7200) as response, raw_path.open(
        "w", encoding="utf-8"
    ) as raw_out:
        status = response.status
        for raw in response:
            decoded = raw.decode(errors="replace").rstrip("\r\n")
            now_epoch = time.time()
            raw_out.write(json.dumps({"epoch": now_epoch, "line": decoded}) + "\n")
            if not decoded.startswith("data:"):
                continue
            body = decoded[5:].strip()
            if body == "[DONE]":
                break
            try:
                chunk = json.loads(body)
            except json.JSONDecodeError:
                continue
            if chunk.get("usage") is not None:
                usage = chunk["usage"]
            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                reasoning_piece = (
                    delta.get("reasoning_content") or delta.get("reasoning") or ""
                )
                content_piece = delta.get("content") or ""
                if reasoning_piece or content_piece:
                    now_mono = time.monotonic()
                    first_token_epoch = first_token_epoch or now_epoch
                    first_token_mono = first_token_mono or now_mono
                    last_token_epoch = now_epoch
                    if reasoning_piece:
                        first_reasoning_mono = first_reasoning_mono or now_mono
                        reasoning.append(reasoning_piece)
                    if content_piece:
                        first_content_mono = first_content_mono or now_mono
                        content.append(content_piece)
                if choice.get("finish_reason") is not None:
                    finish_reason = choice["finish_reason"]
    ended_mono = time.monotonic()
    first_token_mono = first_token_mono or ended_mono
    completion_tokens = int((usage or {}).get("completion_tokens") or 0)
    decode_seconds = ended_mono - first_token_mono
    return {
        "http_status": status,
        "usage": usage,
        "finish_reason": finish_reason,
        "started_epoch": started_epoch,
        "first_token_epoch": first_token_epoch,
        "last_token_epoch": last_token_epoch,
        "wall_seconds": ended_mono - started_mono,
        "time_to_first_token_seconds": first_token_mono - started_mono,
        "time_to_first_reasoning_seconds": (
            None
            if first_reasoning_mono is None
            else first_reasoning_mono - started_mono
        ),
        "time_to_first_text_seconds": (
            None if first_content_mono is None else first_content_mono - started_mono
        ),
        "decode_after_first_token_seconds": decode_seconds,
        "decode_after_first_token_tps": (
            (completion_tokens - 1) / decode_seconds
            if completion_tokens > 1 and decode_seconds > 0
            else None
        ),
        "reasoning": "".join(reasoning),
        "content": "".join(content),
    }


def begin_sampling(args):
    stop = threading.Event()
    samples = []
    sampler = threading.Thread(
        target=sample_metrics, args=(args.base, stop, samples), daemon=True
    )
    sampler.start()
    return stop, samples, sampler


def end_sampling(stop, sampler):
    stop.set()
    sampler.join(timeout=3)


def sample_summary(samples):
    return {
        "peak_running": max((row.get("running") or 0) for row in samples),
        "peak_waiting": max((row.get("waiting") or 0) for row in samples),
        "peak_kv_cache_usage_perc": max(
            (row.get("kv_usage") or 0) for row in samples
        ),
    }


def write_result(output_dir, before, after, result, samples):
    (output_dir / "metrics-before.txt").write_text(before)
    (output_dir / "metrics-after.txt").write_text(after)
    result["metric_samples"] = samples
    (output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")


def repeated_prompt(tokenizer, target, intro, unit, tail, needles=()):
    fixed_tokens = len(
        tokenizer.encode(intro + "".join(needles) + tail, add_special_tokens=False)
    )
    unit_tokens = len(tokenizer.encode(unit, add_special_tokens=False))
    template_allowance = 128
    repeats = max(1, (target - fixed_tokens - template_allowance) // unit_tokens)
    if needles:
        weights = (1, 4, 4, 1)
        regions = [repeats * weight // sum(weights) for weight in weights]
        regions[-1] += repeats - sum(regions)
        text = (
            intro
            + unit * regions[0]
            + needles[0]
            + unit * regions[1]
            + needles[1]
            + unit * regions[2]
            + needles[2]
            + unit * regions[3]
            + tail
        )
    else:
        text = intro + unit * repeats + tail
    return text, fixed_tokens + repeats * unit_tokens + template_allowance


def run_prefill(args, tokenizer, target, needle=False):
    name = "prefill-490k-needle" if needle else "prefill-64k"
    output_dir = args.output_dir / name
    output_dir.mkdir(parents=True, exist_ok=True)
    if needle:
        intro = (
            "Three exceptional records in this archive contain retrieval keys. "
            "Ordinary records contain none. Report all three keys at the end.\n\n"
        )
        unit = (
            "Routine archive entry: technicians inspected drainage, checked boundary "
            "markers, and recorded ordinary seasonal conditions; no retrieval key.\n"
        )
        needles = (
            "\nEXCEPTIONAL ALPHA: the cobalt key is CEDAR-7319.\n",
            "\nEXCEPTIONAL BRAVO: the amber key is LANTERN-4826.\n",
            "\nEXCEPTIONAL CHARLIE: the silver key is HARBOR-9054.\n",
        )
        tail = (
            "\nEND ARCHIVE. Reply exactly as: ALPHA=<key>; BRAVO=<key>; "
            "CHARLIE=<key>."
        )
    else:
        intro = (
            "Read this operational archive. Every entry is routine. At the end, "
            "reply with exactly READY.\n\n"
        )
        unit = (
            "Routine entry: workers checked pumps, labels, access gates, and weather "
            "seals; all readings remained within the operating range.\n"
        )
        needles = ()
        tail = "\nEND ARCHIVE. Reply with exactly READY."
    text, estimate = repeated_prompt(
        tokenizer, target, intro, unit, tail, needles
    )
    payload = request_payload(args, [{"role": "user", "content": text}], target)
    (output_dir / "request.json").write_text(json.dumps(payload, indent=2) + "\n")
    before = metrics_text(args.base)
    stop, samples, sampler = begin_sampling(args)
    try:
        response = stream_chat(args, payload, output_dir / "stream.jsonl")
    finally:
        end_sampling(stop, sampler)
    after = metrics_text(args.base)
    reasoning = response.pop("reasoning")
    content = response.pop("content")
    (output_dir / "reasoning.txt").write_text(reasoning)
    (output_dir / "content.txt").write_text(content)
    prompt_tokens = int((response.get("usage") or {}).get("prompt_tokens") or estimate)
    response.update(
        {
            "test": name,
            "constructed_prompt_tokens_estimate": estimate,
            "prompt_tokens_per_second_to_first_token": (
                prompt_tokens / response["time_to_first_token_seconds"]
            ),
            **sample_summary(samples),
            "response_is_ready": content.strip() == "READY" if not needle else None,
            "needle_hits": (
                {
                    key: key in content
                    for key in ("CEDAR-7319", "LANTERN-4826", "HARBOR-9054")
                }
                if needle
                else None
            ),
        }
    )
    write_result(output_dir, before, after, response, samples)
    return response


def steady_state_throughput(samples, started, ended):
    window = [
        row
        for row in samples
        if started <= row["epoch"] <= ended
        and row.get("generation_tokens_total") is not None
    ]
    if len(window) < 2:
        return None
    seconds = window[-1]["epoch"] - window[0]["epoch"]
    tokens = (
        window[-1]["generation_tokens_total"]
        - window[0]["generation_tokens_total"]
    )
    if seconds <= 0 or tokens < 0:
        return None
    return {
        "window_seconds": seconds,
        "generation_tokens": tokens,
        "generation_tokens_per_second": tokens / seconds,
    }


def run_decode(args, workers):
    name = f"decode-{workers}x"
    output_dir = args.output_dir / name
    output_dir.mkdir(parents=True, exist_ok=True)
    barrier = threading.Barrier(workers)

    def one(index):
        prompt = (
            "Write a rigorous engineering monograph about designing a reliable distributed "
            "job scheduler. Cover requirements, architecture, state machines, failure "
            "recovery, idempotency, fairness, observability, capacity planning, security, "
            "testing, and operational playbooks. Use concrete examples, aim for approximately "
            "6,000 output tokens without padding or repetition, and conclude naturally when "
            f"complete. Independent stream identifier: decode-{workers}x-{index}."
        )
        payload = request_payload(
            args, [{"role": "user", "content": prompt}], 8100 + index
        )
        (output_dir / f"stream-{index}-request.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
        barrier.wait()
        result = stream_chat(args, payload, output_dir / f"stream-{index}.jsonl")
        reasoning = result.pop("reasoning")
        content = result.pop("content")
        (output_dir / f"stream-{index}-reasoning.txt").write_text(reasoning)
        (output_dir / f"stream-{index}-content.txt").write_text(content)
        result.update(
            {
                "stream": index,
                "reasoning_chars": len(reasoning),
                "content_chars": len(content),
                "output_sha256": hashlib.sha256(
                    (reasoning + content).encode()
                ).hexdigest(),
            }
        )
        return result

    before = metrics_text(args.base)
    stop, samples, sampler = begin_sampling(args)
    started = time.monotonic()
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, range(1, workers + 1)))
    finally:
        ended = time.monotonic()
        end_sampling(stop, sampler)
    after = metrics_text(args.base)
    generated = sum(
        int((row.get("usage") or {}).get("completion_tokens") or 0)
        for row in results
    )
    overlap_start = max(row["first_token_epoch"] for row in results)
    overlap_end = min(row["last_token_epoch"] for row in results)
    aggregate = {
        "workers": workers,
        "generated_tokens": generated,
        "batch_wall_seconds": ended - started,
        "batch_makespan_tokens_per_second": generated / (ended - started),
        "steady_state_concurrent": steady_state_throughput(
            samples, overlap_start, overlap_end
        ),
        **sample_summary(samples),
    }
    report = {"test": name, "requests": results, "aggregate": aggregate}
    write_result(output_dir, before, after, report, samples)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8001")
    parser.add_argument("--model", default="pennyroyal")
    parser.add_argument("--tokenizer-path", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reasoning-effort", default="xhigh")
    parser.add_argument("--max-tokens", type=int, default=32768)
    parser.add_argument("--tests", nargs="+", choices=(*TESTS, "all"), required=True)
    args = parser.parse_args()
    selected = list(TESTS) if "all" in args.tests else list(dict.fromkeys(args.tests))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(
        args.tokenizer_path, trust_remote_code=True, local_files_only=True
    )
    results = {}
    for test in selected:
        if test == "prefill-64k":
            results[test] = run_prefill(args, tokenizer, 64000)
        elif test == "prefill-490k-needle":
            results[test] = run_prefill(args, tokenizer, 490000, needle=True)
        elif test == "decode-1x":
            results[test] = run_decode(args, 1)
        else:
            results[test] = run_decode(args, 4)
        print(json.dumps({test: results[test]}, indent=2))
    (args.output_dir / "benchmark-summary.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
