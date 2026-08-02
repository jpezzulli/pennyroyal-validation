# MoET staged reasoning-quality screen

## Decision

MoET completed the full single-pass frozen suite, but Qwen was not started. The frozen stop/go rule requires reporting first because C5 contains one deployment-critical fatal error in the proposed repair. A targeted C5 rerun is the next permitted discriminator.

## Grading

- Raw dimension-weighted qualitative score: **96.16/100**.
- Final case-weighted score after the frozen C5 fatal cap: **87.54/100**.
- Fatal cases: **1/8 (C5)**.
- Confirmed hard loops: **0**.
- Length exhaustions: **0**.
- API/generation errors: **0**.
- Every measured call ended with `finish_reason=stop`.

| Case | Raw | Final | Finding |
|---|---:|---:|---|
| C1 | 96 | 96 | Correct PMTU diagnosis; minor unsupported specificity around DF. |
| C2 | 98 | 98 | Correct authoritative event ordering and uncertainty. |
| C3 | 100 | 100 | Correct integer optimum and infeasibility proof. |
| C4 | 91 | 91 | Correct schedule and lower bound, but substantially overlong and repetitive. |
| C5 | 86 | 35 | Fatal cap: proposed repair does not persist invalid/missing-account outcomes, so later reuse can change outcome or accept changed parameters. |
| C6 | 100 | 100 | Correctly blocks release and rejects distractions. |
| C7 | 100 | 100 | Correct sharp posterior bounds and independence caveat. |
| C8 | 100 | 100 | Correct initial decision and complete revision after correction. |

Dimension scores: correctness 96; evidence discipline 98; contradiction detection 100; constraint preservation 94; technical reasoning 96; unsupported-assumption control 94; confidence calibration 95; revision quality 100; loop behavior 91; final usability 95.

## C5 fatal finding

The response correctly diagnosed most defects, including insufficient-funds idempotency, fingerprint mismatch, missing accounts, negative/self transfers, and canonical account locking. Its replacement nevertheless returns early for invalid inputs and missing accounts without atomically recording the request ID, fingerprint, and terminal result. The frozen requirement says every outcome is idempotent, and the frozen fatal condition covers a proposed repair that retains inconsistent duplicates. A later request can reuse that ID after circumstances or parameters change. The per-case score is therefore capped at 35.

## Runtime results

- Measured requests: **9** (C1-C7 plus both C8 turns).
- Generated tokens: **28,452** by the checkpoint tokenizer.
- Sum of measured wall times: **715.31 s**.
- Aggregate effective generation rate: **39.78 tok/s**.
- Per-request range: **32.52-40.99 tok/s**.
- Measured host power: **416.4 W average / 462 W peak**.
- Measured RTX PRO 6000 power: **144.4 W average / 158.6 W peak**.
- Combined host plus external-GPU power: **560.7 W average / 608.9 W peak**.
- Measured temperature peaks: **63 C CPU package / 44 C GPU**.
- Measured GPU utilization: **64.2% average / 91% peak**.
- Measured RAM/swap peaks: **19.0 GiB / 27.4 GiB**.
- Measured PCIe peaks: **5,368 MiB/s RX / 495 MiB/s TX**.
- No heat guard, hard-loop termination, server error, or reclaim livelock occurred.

Including startup and pack loading, host power peaked at 633 W, CPU packages at 70/74 C, GPU at 44 C, RAM at 155.9 GiB, and swap at 33.9 GiB. These remained below the frozen thermal thresholds. Pack-backed paging produced expected transient swap-in/major-fault activity during startup and resident-plane construction; it did not persist as reclaim livelock during the measured suite.

## Collection integrity

The approved prompts, key, rubric, protocol, launchers, checkpoint configuration, pack manifest, and collector were hashed before launch in `FROZEN-SHA256SUMS`. Complete request JSON, raw SSE lines with monotonic timestamps, reconstructed reasoning and answers, usage, finish state, errors, and loop events are under `moet/raw`. The qualitative packet excluded runtime identity, counts, timing, finish/loop/termination state, and server metadata. Qualitative grades were locked before the operational summary was joined.

