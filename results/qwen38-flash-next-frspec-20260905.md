# Pennyroyal v2.3 — Flash-Next FR-Spec results

Measured September 5–6, 2026, on one NVIDIA RTX PRO 6000 Blackwell at TP1.
v2.3 adds a 65,536-token FR-Spec draft vocabulary while retaining full target
verification and the existing acceptance policy.

Credit to [gabrielolympie/sglang-flashnext-sm120](https://github.com/gabrielolympie/sglang-flashnext-sm120)
for the reduced draft-vocabulary optimization. Pennyroyal uses SGLang's
FR-Spec support with a separately generated map that includes all 21 special
tokens and excludes evaluation cases from its source corpus.

## Configuration and method

| Setting | Value |
|---|---|
| Model | Qwen3.8 Flash-Next ModelOpt NVFP4 |
| SGLang executable | `836206a0adc8ef7aaa49f652230d5577a25014a5` |
| Package | `0.5.19.dev492+g836206a0a` |
| Validation suite | `989230c77459ba636a85b8b5da4cc550f6e1867d` |
| Context / KV capacity | 524,288 / 824,384 tokens |
| Concurrency / page size | Four requests / 64 tokens |
| Native NEXTN MTP | Three steps, top-k 1, four draft tokens |
| Recurrent state | 24 BF16 Mamba slots |
| HiCache / persistence | 32 GiB / NIXL |
| CUDA graphs | Enabled |
| Static memory fraction | 0.981 |

The same checkpoint, executable, and sampling settings were used across the
baseline and FR-Spec runs. The extra draft head used 320 MiB without reducing
KV capacity or context. Map SHA-256:
`becfa41d394b86c26c632bea8f3c6ea64bbb76d7b238d8673c06afae21269f25`.

Performance tests used `performance/openai_chat_benchmarks.py` through
ordinary OpenAI Chat Completions after warmups, with 1,024 server-reported
completion tokens per stream.

- **Single-request decode:** tokens per second after the first token.
- **Single-request whole-request rate:** completion tokens divided by total request duration.
- **Four-request aggregate:** all completion tokens divided by synchronized
  batch duration, including first-token delay and the slowest stream.

Per-stream rates are not additive. Server token usage is authoritative.

## Decode throughput

| Configuration | Samples per metric | Single-request decode, median | Single-request whole-request rate, median | Four-request aggregate, median |
|---|---:|---:|---:|---:|
| v2.1.2 baseline, run 1 | 3 | 156.79 tok/s | 151.17 tok/s | 417.92 tok/s |
| v2.3 FR-Spec, initial measurements | 3 | 165.33 tok/s | 157.16 tok/s | 447.83 tok/s |
| v2.1.2 baseline, run 2 | 3 | 147.15 tok/s | 140.88 tok/s | 427.91 tok/s |
| **v2.3 FR-Spec** | **6** | **171.93 tok/s** | **164.40 tok/s** | **447.04 tok/s** |

The six-sample v2.3 medians are **9.7–16.8% higher for single-request decode**
and **4.5–7.0% higher for four-request aggregate** than the two baseline
medians. Initial FR-Spec measurements showed +5.4% and +7.2%, respectively,
against baseline run 1.

v2.3 single-request samples: 170.84, 173.10, 169.12, 173.01, 158.15, 177.23 tok/s.
Four-request aggregate samples: 447.84, 438.10, 462.82, 446.24, 459.70, 439.08 tok/s.
The pooled per-stream four-request decode median was 122.67 tok/s.

Tests ran sequentially, with the two baseline runs on separate boots.
Run-to-run variation was material; these are measured comparisons, not
randomized confidence intervals or guaranteed gains. Earlier model/runtime
campaigns are separate measurements.

## Cold prefill

| Prompt | v2.1.2 TTFT | v2.3 FR-Spec TTFT | Result |
|---|---:|---:|---|
| 63,864 tokens | 4.969 s | 4.886 s | Exact READY |
| One 489,879-token prompt | 61.070 s | 61.319 s | All three separated needles exact |

Both configurations used fresh cache namespaces. Cold prefill was essentially
unchanged: approximately 12.9–13.1K prompt tok/s at 64K and 8.0K prompt tok/s
at 490K. These are prefill measurements, not decode throughput.

## Reasoning

Two warmups preceded nine measured requests using the
`three-user-1-3-3-1` schedule. The launcher supplied the reasoning defaults.
All nine requests stopped naturally, producing 131,770 completion tokens.
No loop or fatal-error score caps applied.

**Qualitative score: 98.52/100. Final score: 98.52/100.**

| Case | Score /100 | Assessment |
|---|---:|---|
| C1 | 97.28 | Correct MTU of 1,404; long and repetitive presentation. |
| C2 | 96.74 | Correct causal diagnosis; unnecessary hypothesis about an intermediate event. |
| C3 | 98.91 | Correct 6A/5B/4048 optimum and infeasibility argument; some repetition. |
| C4 | 100.00 | Correct schedule, optimality proof, and X/19 consequence. |
| C5 | 96.74 | Correct claim-before-account, idempotency, and canonical locking; unnecessary rollback branch and excessive length. |
| C6 | 100.00 | Correct no-release decision. |
| C7 | 100.00 | Correct sharp bounds of 5/14 through 1, with endpoint constructions; 28/37 correctly depends on an added assumption. |
| C8, including correction | 98.50 | Correct revision from X to W; initial confidence was not explicit. |

| Dimension | Weight | Average /4 |
|---|---:|---:|
| Correctness | 24 | 4.00 |
| Evidence discipline | 10 | 4.00 |
| Contradiction detection | 10 | 4.00 |
| Constraint preservation | 10 | 4.00 |
| Technical reasoning | 14 | 4.00 |
| Unsupported assumptions | 8 | 3.72 |
| Confidence calibration | 6 | 3.90 |
| Revision quality | 8 | 4.00 |
| Loop behavior | 6 | 3.86 |
| Final-answer usability | 4 | 3.44 |

Case weights were 14/12/14/14/16/10/10/10. The suite's scoring tool applied
the mechanical caps after qualitative grading; none was triggered.

Grading used anonymized paired outputs. Scores were fixed before configuration
metadata was revealed and mechanical caps were applied. This was an
AI-assisted review, not an independent external panel. The review covered
all final answers and corrections plus selected reasoning passages, not every
reasoning token. An archived control scored 97.62 under the same review, but
used an older runtime and sequential execution; it does not establish a
reasoning-quality improvement from FR-Spec.

### Reasoning throughput and memory

| Running requests | Samples | Aggregate throughput, median | Acceptance length, median | Acceptance rate, median |
|---|---:|---:|---:|---:|
| 1 | 948 | 145.07 tok/s | 2.00 | 0.33 |
| 2 | 105 | 277.53 tok/s | 2.19 | 0.40 |
| Exactly 3 | 128 | 353.94 tok/s | 2.13 | 0.38 |

These are scheduler interval samples grouped by the reported running count,
not time-weighted or per-request rates. Transition intervals can include
previous occupancy. All samples reported CUDA graphs enabled.

Sampled GPU memory peaked at 95,499 MiB used, with 1,793 MiB free.
After concurrent restoration, memory use was 95,517 MiB; after the two
long-context continuation turns, it was 95,537 MiB. KV capacity remained
824,384 tokens.

## Tools and agent workflows

| Measurement | Result |
|---|---:|
| Invocations | 30 |
| Literal automatic checks | 27/30 |
| Exact tool selections and arguments | 29/30 |
| Parseable responses | 30/30 |
| Runtime errors | 0 |
| Clean workflows | 29 |
| Workflows with a redundant read-only call | 1 |
| Reviewed response discipline | 28/30 |

Both invalid-date answers were correct but used wording that missed the
literal checker; one unnecessarily repeated the read-only validation call.
No consequential tool execution failure occurred.

Two response-quality issues were separate from tool execution: an invoice
answer rejected prompt injection but added prose despite an exact-output
instruction, and a deployment answer overstated rollback and blast-radius
guarantees. The response-discipline score reflects those issues.
A matching full baseline tool run was not collected, so these differences
cannot be attributed specifically to FR-Spec.

The agent-workflow test passed in six model turns with five tool calls,
including revision and final inspection of the requested artifact.

## Vision and natural decode

Vision passed automatic and manual spatial/claim-separation checks. It
returned 377 tokens and stopped naturally within the 1,024-token limit.

The natural-decode test returned exactly 3,072 tokens and all 3,072 direct
token IDs. Its automatic check failed because the collector read
`token_ids` while SGLang returned `response_token_ids`. The numeric record
includes the observed count and hash alongside the failed automatic result.

A second evaluator limitation affects saved request snapshots: the collector
keeps mutable message-list references, so later turns can appear in earlier
saved snapshots. HTTP requests were serialized before those later additions;
this does not mean the model received future turns. Both collector issues
are outside the runtime change in v2.3.

## NIXL persistence and long-context continuation

Tests covered fresh cache writes, reuse after restart, switching between
FR-Spec and non-FR configurations, and representation-specific namespace
isolation.

| Configuration after restart | 64K restored tokens / TTFT | 490K restored tokens / TTFT |
|---|---|---|
| v2.1.2 Flash-Next | 63,808 / 1.193 s | 489,856 / 6.592 s |
| v2.3 Flash-Next FR-Spec | 63,808 / 1.213 s | 489,856 / 5.940 s |
| 27B FP8/DFlash2 | 63,808 / 1.804 s | 489,856 / 11.247 s |

All READY and three-needle checks passed. Each restored request loaded two
Mamba states. The v2.3 490K request loaded 7,046,561,824 bytes across the
registered pools, establishing storage restoration rather than only
GPU-resident prefix reuse.

Four requests—two copies each of the saved 64K and 490K prompts—completed
correctly in 9.396 seconds. Counters recorded 553,664 NIXL-hit tokens,
553,664 device-hit tokens, 553,664 KV load-back tokens, four Mamba states,
and 8,067,100,736 bytes transferred across the pools. Duplicate requests
reused restored prefixes; this was not four independent full disk transfers.

Two further turns extended the restored 490K conversation. The first changed
one requested value while preserving the other two; the second withdrew that
change. Both returned exact JSON and stopped naturally:

| Turn | Prompt tokens | Completion tokens | Duration |
|---|---:|---:|---:|
| Apply override | 489,984 | 106 | 5.210 s |
| Withdraw override | 490,081 | 111 | 4.791 s |

A subsequent restart check again passed nine startup/API checks and restored
489,856 tokens with all three needles correct.

Missing-sidecar and corrupt-manifest fault injection were not repeated.
The cache remains disposable storage, not a transactional persistence system.

## 27B compatibility

The unchanged 27B FP8/DFlash2 launcher passed nine startup/API checks,
64K/490K prefill, single-request and four-request decode, and NIXL restart
restoration. It retained CUDA graphs and its 1,118,784-token KV pool.
A single compatibility measurement recorded 106.73 tok/s single-request
decode and 363.81 tok/s four-request aggregate; no 27B speed gain is claimed.
Full 27B reasoning/tool tests were not repeated because its executable and
launcher were unchanged.

## Data and reproducibility

The [numeric record](qwen38-flash-next-frspec-20260905.json) includes sample
timings, server usage, acceptance, memory, scores, and restoration counters.
Additional kernel configurations in that file are marked as outside v2.3;
they are not included in the release throughput comparison. Full request
streams and service logs are not distributed with this summary.

[Runtime and launch instructions](https://github.com/jpezzulli/sglang-rtxpro6000)
and [Pennyroyal v2.3 release](https://github.com/jpezzulli/sglang-rtxpro6000/releases/tag/pennyroyal-v2.3.0).
