# Qwen staged reasoning-quality screen

## Decision

Qwen completed the full frozen single-pass suite. Native LvLLMDS4 was not started. Under the frozen grading rules, Qwen scored below MoET because Qwen entered a confirmed C5 hard loop and produced no visible answer, while MoET's C5 answer was usable but contained a fatal idempotency-ownership error.

## Grading

- Raw dimension-weighted qualitative score: **92.14/100**.
- Raw case-weighted score: **90.04/100**.
- Final case-weighted score after the frozen C5 loop cap: **82.84/100**.
- Fatal cases: **1/8 (C5)**.
- Confirmed hard loops: **1**.
- Length exhaustions: **0**.
- API/generation errors: **0**.
- Eight measured calls ended with `finish_reason=stop`; C5 was terminated by the frozen loop detector.

| Case | Raw | Final | Finding |
|---|---:|---:|---|
| C1 | 98 | 98 | Correct PMTU diagnosis, boundary, capture reconciliation, alternatives, fix, and verification. |
| C2 | 94 | 94 | Correct authoritative ordering and uncertainty; minor unsupported speculation appeared among the unknowns. |
| C3 | 98 | 98 | Correct integer optimum, constraint proof, and reduced-capacity infeasibility proof. |
| C4 | 78 | 78 | Correct schedule and lower bound, but reasoning entered a long repeated self-check cycle and duplicated the final answer. |
| C5 | 65 | 20 | Confirmed hard-loop cap: sound internal diagnosis and intended fix, but no visible final answer was produced. |
| C6 | 100 | 100 | Correctly blocks release and rejects all distractions. |
| C7 | 100 | 100 | Correct sharp posterior bounds and independence caveat. |
| C8 | 100 | 100 | Correct initial result and complete multi-turn revision. |

Dimension scores: correctness 95; evidence discipline 84; contradiction detection 100; constraint preservation 96; technical reasoning 94; unsupported-assumption control 98; confidence calibration 82; revision quality 100; loop behavior 69; final usability 82.

## C5 loop finding

C5 reasoning identified the important failures and explicitly converged on the sound design: atomically own the request ID and fingerprint, persist invalid, missing-account, insufficient, and successful outcomes, validate parameter reuse, and lock both accounts in canonical order. It then repeated a 392-token block four consecutive times. The frozen detector stopped collection at 12,298 local tokens after 111.96 seconds. No visible final answer was emitted, so the confirmed-reasoning-loop cap of 20 applies.

C4 also contained substantial repeated self-checking, but it did not meet the frozen hard-loop termination criteria and eventually returned the correct usable answer. It was penalized qualitatively rather than mechanically capped.

## Runtime results

- Measured requests: **9** (C1-C7 plus both C8 turns).
- Generated tokens: **58,923** by the deployed Qwen tokenizer.
- Sum of measured wall times: **536.47 s**.
- Aggregate effective generation rate: **109.83 tok/s**.
- Per-request effective range: approximately **102.5-115.1 tok/s**.
- Measured host power: **469.5 W average / 566 W peak**.
- Measured RTX PRO 6000 power: **229.1 W average / 291.0 W peak**.
- Combined host plus external-GPU power: **698.7 W average / 833.0 W peak**.
- Measured temperature peaks: **67 C CPU package / 51 C GPU**.
- Measured GPU utilization: **82.9% average / 100% peak**.
- Measured VRAM peak: **95,073 MiB**.
- Measured RAM/swap peaks: **19.4 GiB / 27.7 GiB**.
- Measured PCIe peaks: **76 MiB/s RX / 47 MiB/s TX**.
- No heat guard, reclaim livelock, request error, or 32K exhaustion occurred.

Including startup, combined host plus external-GPU power peaked at 909.4 W, CPU packages at 68 C, GPU at 51 C, RAM at 19.5 GiB, and swap at 28.1 GiB. Startup and measured operation remained below the frozen thermal thresholds.

The endpoint used `max_tokens=32768` for every measured response. No temperature, top-p, top-k, seed, reasoning-effort, tool, stop, or formatting field was sent in a request. The unchanged launcher supplied model defaults of temperature 0.6, top-k 20, top-p 0.95, high thinking, and two-token MTP.

## MoET comparison

| Result | MoET | Qwen |
|---|---:|---:|
| Raw dimension-weighted score | 96.16 | 92.14 |
| Final case-weighted score | 87.54 | 82.84 |
| Confirmed hard loops | 0 | 1 |
| Generated local tokens | 28,452 | 58,923 |
| Measured wall time | 715.31 s | 536.47 s |
| Effective generation rate | 39.78 tok/s | 109.83 tok/s |
| Combined power average | 560.7 W | 698.7 W |
| CPU / GPU peak temperature | 63 / 44 C | 67 / 51 C |

Qwen was **2.76x faster by generated-token throughput** but used about **25% more combined instantaneous power** during measured requests. Qwen still completed the measured suite sooner despite generating more than twice as many tokens. Under the frozen quality rubric, MoET remains the reasoning winner; both candidates have a material C5 weakness, but of different kinds.

## Collection integrity and final state

The original frozen hashes passed before launch. Complete request JSON, raw SSE lines with monotonic timestamps, reconstructed reasoning and answers, usage, finish state, errors, loop events, server log, and one-second telemetry are preserved under `qwen`. The qualitative packet excluded runtime identity, token counts, timing, throughput, finish/loop/termination state, and server metadata. Scores were locked before operational metrics were joined.

Qwen was stopped after collection. Port 8001 is free. LvLLMDS4 was not started.
