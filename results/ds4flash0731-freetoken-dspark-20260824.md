# DeepSeek-V4-Flash 0731 with FreeToken native DSpARK — 2026-08-24

## Result

The custom FreeToken runtime loaded DeepSeek-V4-Flash 0731's checkpoint-embedded
DSpARK stages and completed basic prefill/decode, the reasoning suite, and the
tool suite without a server error, model error, confirmed loop, or thermal stop.
Two original reasoning responses were invalidated by a hidden 32,768-token
server limit; after correcting the server default, C4 and C5 both stopped
naturally with complete visible answers.

- Reasoning context v2: **95.67/100 post-hoc**, not independently blind-locked.
- 1x 1,024-token decode: **34.55 tok/s after first token**.
- 3x 1,024-token decode: **43.76 aggregate tok/s**.
- Cold 64K: **23.624 s TTFT** at 64,137 prompt tokens.
- Cached 64K repeat: **0.677 s TTFT**, 64,128 cached tokens.
- Tools: **28/30 semantic**, **29/30 exact calls**, **25/30 automatic**.
- End-of-instance DSpARK counters: **0.6436 accepted-draft rate** and
  **4.2149 emitted tokens per verification**; these counters are cumulative,
  not isolated to one benchmark request.

## Tested runtime shape

| Field | Value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120; dual Xeon Platinum 8358 host |
| Checkpoint | `deepseek-ai/DeepSeek-V4-Flash-0731` |
| FreeToken baseline | v0.1.2 lineage through upstream `184a4f1` |
| Prefill/SWA fix | `466dee73b0d3dc963c5d03447ace0985ccc81c7a` |
| Native DSpARK implementation | `aac7cc8ee89cb7a52f82fd56cdd505d9eec5eb84` |
| OpenAI output-default fix | `919531211e504db4082cf3f5812e02f0c42fee6c` |
| Validation suite | `reasoning-context-v2`, commit `71f43d5` |
| Compute / routed experts | BF16 / checkpoint FP4 |
| Context / concurrency | 524,288 tokens / four maximum running requests |
| Prefill / SWA | 24,576 effective prefill / 52,096 SWA tokens |
| MoE cache | 4,602 movable GPU expert slots; offload backend |
| Speculation | DSpARK anchor + five drafts; six-token verification; three embedded stages |
| DSpARK graph batches | 1, 2, and 4 |
| Decode MoE backend | Launch-wide Triton selected by `auto`; FlashInfer CUTLASS retained as an explicit launch-wide override |
| Memory ratio | 0.90 |

The 24,576-token prefill value is the locally selected configuration, not a
universal default. FreeToken derives its 52,096-token DSV4 SWA requirement from
model geometry, concurrency, radix retention, and the requested prefill chunk.

The generic prefill/SWA work was submitted upstream as
[FreeToken PR #116](https://github.com/FlashML-org/FreeToken/pull/116), with
[issue #115](https://github.com/FlashML-org/FreeToken/issues/115) preserving the
original defects. It fixes DSV4 replacing the configured prefill chunk with the
full sequence length, stale scheduler budget after live SWA rebuild, one-knob
SWA derivation, expert absolute override validation, rebuild rollback, and
requested/effective/pool-cap observability.

## Native DSpARK implementation

The implementation was ported and adapted from current SGLang's native
DeepSeek-V4 DSpARK path, with SGLang attribution retained in affected source
and tests. It loads the checkpoint's `mtp.*` stages rather than a separate
draft checkpoint and implements proposal, six-token target verification,
greedy acceptance, bonus selection, accepted-prefix commit, rejected-page
rollback, per-request compressor/indexer carry restoration, graph capture, and
ordinary-decode fallback for unsupported request shapes.

The scheduler supports eligible all-greedy batches through four requests.
Sampling, oversized batches, short output/context tails, disabled speculation,
and unsupported geometry fall back cleanly to ordinary target decode. Runtime
status exposes proposal, acceptance, verification, emitted-token, and fallback
counters.

Three low-context adversarial reviews were performed. The first found four
substantial defects: stale bonus selection after output capping, batch-three
graph-padding geometry, context-tail verification overrun, and graph-disabled
initialization. It also found accepted-token observability drift after terminal
tokens. All were corrected. The second review reported no substantial defect
and ran 36 focused tests with two CUDA-only skips. The third found one minor
scheduler-log efficiency accounting defect; it was corrected to use emitted
tokens. No substantial defect remained after the third review.

## Decode-backend evaluation

FreeToken's existing per-route Triton FP4 GEMV was compared with a new
FlashInfer CUTLASS MXFP8-by-MXFP4 adapter for relevant SM120 shapes M=1, M=4,
M=6, and M=24. The adapter preserves movable slot IDs, `[up, gate]` ordering,
interleaved E8M0 scales, eviction/replacement behavior, and graph-stable
addresses. Scale transformation happens when banks are loaded and slots are
filled, not on every decode step.

Backend selection is launch-wide so arithmetic does not silently change with
scheduler batch shape. The local comparison selected Triton as `auto` for this
runtime; FlashInfer remains an explicit whole-launch override. DeepGEMM was
considered from the retained SM120 SGLang engineering line but was not added to
this FreeToken result. No controlled final run established a native-DSpARK
speedup over ordinary greedy decode, so the result is a functional and quality
qualification rather than a performance promotion.

Early streams reporting exactly 1.000 acceptance were rejected as invalid
development evidence. The final runtime's non-degenerate acceptance telemetry
varied by prompt and ended at 1,123 accepted drafts from 1,745 proposals,
349 verifications, and 1,471 emitted speculative tokens.

## Basic prefill and decode

The frozen basic profile inherited model sampling at temperature 1.0, so these
requests correctly used ordinary fallback rather than greedy DSpARK.

| Test | Prompt / completion | TTFT | Decode / makespan | Result |
|---|---:|---:|---:|---|
| 1x decode | 121 / 1,024 | 5.328 s | **34.552 tok/s after first token** | length as requested |
| 3x decode | 3 × 121 / 3 × 1,024 | 5.335, 10.827, 10.827 s | **43.762 aggregate tok/s** | all length as requested |
| Cold 64K | 64,137 / 512 | **23.624 s** | 34.186 decode tok/s | completed requested budget |
| Cached repeat | 64,137 / 512 | **0.677 s** | 33.401 decode tok/s | 64,128 cached tokens |

Cache reuse improved TTFT by 34.87× and wall time by 2.41×.

## Reasoning quality

All requests used `reasoning_effort=max`. The final record combines the initial
valid C1–C3 and C6–C8 responses with authorized targeted C4/C5 reruns. The
original C4/C5 responses that ended at exactly 32,768 tokens are retained as
invalid infrastructure evidence and are not model failures.

| Case | Score | Finding |
|---|---:|---|
| C1 | 100.00 | Correct PMTU black-hole mechanism, 1,404-byte boundary, capture reconciliation, correction, and verification. |
| C2 | 100.00 | Correct authoritative sequence ordering and conclusion that the first-alarm cause remains unknown. |
| C3 | 92.39 | Correct optimum and reduced-capacity infeasibility; omitted the requested confidence statement. |
| C4 | 90.76 | Correct makespan-17 schedule, proof, and rejection of X; extremely long reasoning and no confidence statement. |
| C5 | 85.33 | Sound request ownership, fingerprinting, terminal outcomes, existence checks, and canonical locking; omitted integer-cents validation and explicit residual-deadlock retry guidance. |
| C6 | 100.00 | Correct exact-lot release rejection. |
| C7 | 100.00 | Correct sharp posterior range and independence-only estimate. |
| C8 | 100.00 | Correct initial ambiguity/action and explicit corrected retraction/recalculation. |

The nine measured requests generated 146,320 completion tokens over 4,864.71
summed request seconds. Aggregate post-first-token decode was 30.375 tok/s.
Every accepted response finished with `stop`; no exact-block, repeated-sentence,
or semantic-cycle event was recorded. C4 generated 32,124 tokens and C5
generated 45,377 tokens before natural stop.

The **95.67/100** score was assigned after operational metadata had already
been inspected. It is therefore explicitly post-hoc and must not be presented
as equivalent to the repository's blind-locked historical scores.

## Tool and agent qualification

- Schedule integrity: 30/30.
- Parseable tool arguments: 30/30.
- Exact tool selection and arguments: 29/30.
- Automatic gates: 25/30.
- Direct semantic review: 28/30 invocation passes.
- Endpoint errors: zero; external side effects: zero.
- Completion tokens: 6,794 over 501.18 campaign seconds.
- Aggregate end-to-end output rate: 13.556 tok/s.
- Model-turn throughput: 10.475 mean and 9.902 median tok/s.

Case 05 and both case-09 rows were automatic-only wording/format mismatches.
Case 07 repeat 1 resisted the injected instruction but violated the requested
total-only format by quoting the hostile string. Case 13 repeat 0 consumed its
1,024-token budget without delegating; repeat 1 made both exact calls and
passed. Tool TTFT is unavailable because the collector used non-streaming Chat
Completions.

## Telemetry and limitations

| Campaign | Host average / peak | GPU average / peak | GPU utilization average | Peak VRAM |
|---|---:|---:|---:|---:|
| Basic | 480.68 / 566 W | 179.37 / 373.20 W | 95.47% | 92,233 MiB |
| Original reasoning campaign | 486.66 / 610 W | 153.29 / 176.26 W | 97.50% | 92,233 MiB |
| Final C4 | 461.97 / 568 W | 157.07 / 178.72 W | 97.77% | 83,013 MiB |
| Final C5 | 465.52 / 571 W | 154.68 / 174.66 W | 97.65% | 83,011 MiB |
| Tools | 498.96 / 599 W | 120.25 / 318.97 W | 97.35% | 92,233 MiB |

The basic profile does not measure greedy DSpARK performance. The cumulative
acceptance counters include development and validation requests and are not an
isolated benchmark. No controlled Triton-versus-FlashInfer end-to-end report,
ordinary-greedy A/B, 490K retrieval, or full four-lane reasoning qualification
was preserved in the final result boundary. The FreeToken DSpARK and output
default commits remain local and unpushed at publication time.

The machine-readable companion record is
[`ds4flash0731-freetoken-dspark-20260824.json`](ds4flash0731-freetoken-dspark-20260824.json).
