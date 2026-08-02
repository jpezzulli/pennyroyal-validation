#!/usr/bin/env python3
import http.client
import json
import time
from pathlib import Path

output_dir = Path(
    "/opt/ai-artifacts/logs/"
    "moet-mapped-w2-clean-validation-20260802-005954/final"
)
payload = {
    "model": "pennyroyal",
    "messages": [{
        "role": "user",
        "content": (
            "For an inference throughput test, write a continuous sequence "
            "of concise, distinct observations about elementary arithmetic "
            "and logic. Keep writing without a conclusion until the output "
            "limit is reached."
        ),
    }],
    "max_tokens": 1024,
    "ignore_eos": True,
    "stream": True,
    "stream_options": {"include_usage": True},
}
(output_dir / "decode-1024-request.json").write_text(
    json.dumps(payload, indent=2) + "\n")

connection = http.client.HTTPConnection("127.0.0.1", 8001, timeout=900)
started = time.perf_counter()
started_epoch = time.time()
connection.request(
    "POST", "/v1/chat/completions",
    body=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
response = connection.getresponse()
headers_at = time.perf_counter()
raw_lines = []
events = []
first_token_at = None
finish_reasons = []
usage = None
reasoning = []
content = []

while True:
    line = response.readline()
    if not line:
        break
    raw_lines.append(line)
    stripped = line.strip()
    if not stripped.startswith(b"data: "):
        continue
    data = stripped[6:]
    if data == b"[DONE]":
        break
    event = json.loads(data)
    events.append(event)
    if event.get("usage"):
        usage = event["usage"]
    for choice in event.get("choices", []):
        delta = choice.get("delta") or {}
        pieces = []
        for key, destination in (("reasoning", reasoning),
                                 ("content", content)):
            value = delta.get(key)
            if value:
                destination.append(value)
                pieces.append(value)
        if pieces and first_token_at is None:
            first_token_at = time.perf_counter()
        if choice.get("finish_reason") is not None:
            finish_reasons.append(choice["finish_reason"])

ended = time.perf_counter()
ended_epoch = time.time()
(output_dir / "decode-1024-response.sse").write_bytes(b"".join(raw_lines))
(output_dir / "decode-1024-events.json").write_text(
    json.dumps(events, indent=2) + "\n")
(output_dir / "decode-1024-reasoning.txt").write_text("".join(reasoning))
(output_dir / "decode-1024-content.txt").write_text("".join(content))

completion_tokens = (usage or {}).get("completion_tokens")
decode_seconds = (
    ended - first_token_at if first_token_at is not None else None
)
summary = {
    "http_status": response.status,
    "started_epoch": started_epoch,
    "ended_epoch": ended_epoch,
    "response_headers_seconds": headers_at - started,
    "ttft_seconds": (
        first_token_at - started if first_token_at is not None else None
    ),
    "wall_seconds": ended - started,
    "decode_seconds_after_first_token": decode_seconds,
    "completion_tokens": completion_tokens,
    "decode_tokens_per_second_after_first_token": (
        (completion_tokens - 1) / decode_seconds
        if completion_tokens and completion_tokens > 1 and decode_seconds
        else None
    ),
    "end_to_end_tokens_per_second": (
        completion_tokens / (ended - started)
        if completion_tokens else None
    ),
    "finish_reasons": finish_reasons,
    "usage": usage,
    "reasoning_characters": len("".join(reasoning)),
    "content_characters": len("".join(content)),
    "sse_event_count": len(events),
}
(output_dir / "decode-1024-summary.json").write_text(
    json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
