# Frozen staged execution protocol

- Endpoint: `POST http://127.0.0.1:8001/v1/chat/completions`.
- Measured payload fields: `model=pennyroyal`, frozen `messages`, `max_tokens=65536`, `stream=true`, and `stream_options.include_usage=true`.
- The 65,536-token ceiling applies uniformly to every measured reasoning case. It was raised on 2026-08-15 after Qwen3.8-27B reached the previous 32,768-token ceiling on C5 before producing a complete answer. Historical 32K runs remain valid records of the earlier contract.
- A targeted recovery or confirmation rerun may select exactly one measured case with `--case CASE_ID`; targeted runs skip the two warm-ups and must use a separate output directory.
- Omit temperature, top-p, top-k, seed, request-level reasoning effort, tools, tool choice, stop sequences, and response formatting.
- Run MoET first: two unscored warm-ups, then C1-C7 once and C8 first/correction turns once (nine measured requests).
- Candidate context is fresh for every case. C8 correction context contains only system, C8 first user turn, its returned assistant response, and the frozen correction.
- Preserve exact requests, raw SSE chunks with monotonic timestamps, reconstructed reasoning/content, usage, finish reason, timing, errors, and loop events.
- Hard loop termination: an identical contiguous 64-1024-token block repeated immediately four times, or one normalized sentence of at least eight words repeated ten consecutive times.
- Flag but do not auto-terminate three distinct recurrences of highly similar 256-token reasoning windows (5-gram Jaccard >= 0.85) for blinded confirmation.
- Qualitative graders see response text only, without token, finish, timing, loop, termination, server, order, or runtime metadata. Apply objective caps after scores lock.
- Thermal guard: pause at CPU package >=85 C or GPU >=80 C, preserve any partial response, allow cooling, and explicitly record any recovery request.
- Stop before Qwen and report if MoET meets the frozen deficiency criteria. Otherwise grade and report MoET before any Qwen start.
