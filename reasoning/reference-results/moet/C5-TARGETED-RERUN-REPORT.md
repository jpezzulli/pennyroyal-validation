# MoET targeted C5 rerun

## Decision

**STOP. Qwen was not started.** The single permitted rerun repeated the deployment-critical C5 defect, so the frozen stop/go condition was not satisfied.

## Blind grading

- Qualitative raw C5 score: **86/100**.
- Frozen case-specific fatal cap: **35/100**.
- Final C5 score: **35/100**.
- Fatal errors: **1**.

The answer correctly diagnosed the unsafe fast-path lookup, fingerprint mismatch, missing-account risk, invalid values, insufficient-funds persistence, unique-conflict rollback, and opposite-direction deadlock. It also proposed canonical account locking and persisted `insufficient` and `ok`.

The proposed repair nevertheless returns invalid-amount, identical-account, and missing-account outcomes without first atomically claiming and persisting the request ID, request fingerprint, and terminal result. Those outcomes can change on retry or allow a later call with changed parameters to become the owner. This repeats the original fatal defect and fails the explicit requirement that request ownership and idempotency be preserved for every outcome.

Qualitative grading used only the anonymized response text. Runtime identity, counts, timing, finish state, loop state, and server metadata were revealed only after the grade was locked.

## Collection and operational result

- Measured requests: **1 targeted C5 rerun**, preceded by the same two approved warm-ups.
- Endpoint payload: frozen system and C5 messages, `model=pennyroyal`, `max_tokens=32768`, streaming enabled with usage; no request-level sampling overrides.
- API usage: **494 prompt tokens, 7,540 completion tokens**.
- Local checkpoint-tokenizer count: **7,501 generated tokens**.
- Wall time: **189.64 s**.
- Effective generation rate: **39.76 API tokens/s** (**39.55 local tokens/s**).
- Finish: **stop**; no error, hard loop, semantic-cycle flag, heat stop, or 32K exhaustion.
- C5 host power: **442.8 W average / 532 W peak**.
- C5 RTX PRO 6000 power: **143.1 W average / 154.4 W peak**.
- C5 combined host plus external-GPU power: **585.9 W average / 667.9 W peak**.
- C5 temperature peaks: **61 C CPU package / 40 C GPU**.
- C5 GPU utilization: **63.7% average / 72% peak**.
- C5 VRAM: **96,859 MiB**; RAM peak **16.4 GiB**; swap peak **29.9 GiB**.
- C5 PCIe peaks: **5,363 MiB/s RX / 494 MiB/s TX**.

Across startup plus the rerun, observed peaks were 75 C CPU, 40 C GPU, 153.5 GiB RAM, 96.0 GiB swap, 765 W host power, and 828 W combined host plus external-GPU power. Checkpoint loading produced transient paging and major faults but completed; no thermal guard fired.

## Integrity and service state

All original frozen hashes passed before startup. The targeted collector imported the exact frozen C5 data and original streaming/loop implementation. Complete request JSON, raw SSE with timestamps, reconstructed response, usage, finish state, loop events, telemetry, launcher log, anonymized grading packet, provenance, and hashes are preserved under this directory.

MoET was stopped after collection. Port 8001 is free. Qwen was not launched.
