# Pennyroyal 2.3 — Flash-Next FR-Spec qualification

Measured September 5–6, 2026; published September 6 after release approval.
This promotes frozen FR-Spec RC1, not the excluded BF16 low-M kernel.
Same Flash-Next ModelOpt NVFP4 checkpoint throughout the baseline/FR arms;
local checkpoint identity and placement remain local operational evidence.
Executable `836206a0adc8ef7aaa49f652230d5577a25014a5`, package
`0.5.19.dev492+g836206a0a`; no new shared-runtime code is installed.

Credit to [gabrielolympie/sglang-flashnext-sm120](https://github.com/gabrielolympie/sglang-flashnext-sm120)
for the reduced draft-vocabulary work that prompted this adoption. Penny
uses existing SGLang FR-Spec with its own non-evaluation-source 65,536-ID map,
including all 21 special tokens. Full target vocabulary and acceptance policy
are unchanged; no bit-for-bit sampled-output parity claim.

One RTX PRO 6000, TP1, 524,288 context, 824,384 KV tokens, page64, C4,
24 BF16 Mamba slots, native NEXTN3/1/4, full graphs,32GiB HiCache/NIXL,
0.981 static fraction. The320MiB extra draft head fit without a pool cut.
Map SHA256: `becfa41d394b86c26c632bea8f3c6ea64bbb76d7b238d8673c06afae21269f25`.

## Controlled timing — all original samples retained

Unmodified `performance/openai_chat_benchmarks.py` from
**jpezzulli/pennyroyal-validation**, verified current main
`989230c77459ba636a85b8b5da4cc550f6e1867d`. The isolated checkout remains clean.
Ordinary `/v1/chat/completions`, ordinary warmups before measurements, same
client parameters and 1,024 output tokens per timed stream. C1 below is
client post-first-token rate; C4 is **aggregate synchronized request makespan**,
including first-token delay, not a pure decode rate or sum of stream rates.
Server usage is authoritative. Per-stream timings, telemetry and request-time
stats are preserved, not substituted with local tokenizer estimates.

| Arm | Samples C1/C4 | C1 post-first tok/s, median | C1 request-makespan tok/s, median | C4 aggregate request-makespan tok/s, median |
|---|---:|---:|---:|---:|
| Initial released baseline | 3/3 | 156.79 | 151.17 | 417.92 |
| Initial FR-Spec | 3/3 | 165.33 | 157.16 | 447.83 |
| BF16-only, held | 3/3 | 164.69 | 156.11 | 417.18 |
| Released return after reboot | 3/3 | 147.15 | 140.88 | 427.91 |
| Retained FR-Spec after restart | 6/6 | **171.93** | **164.40** | **447.04** |
| Combined | incomplete | — | — | — |

Retained FR-Spec C1 samples: 170.84,173.10,169.12,173.01,158.15,177.23.
C4 aggregate samples:447.84,438.10,462.82,446.24,459.70,439.08.
Its pooled per-stream C4 post-first median is122.67tok/s, distinct from
the447.04tok/s aggregate makespan metric. All arms retained824384 KV tokens.

The retained median is about **9.7–16.8% above the two baseline C1 medians**
and **4.5–7.0% above their C4 aggregate medians**. The initial FR-Spec arm
showed +5.4% C1 and +7.2% C4 against the initial baseline. These are measured
session comparisons, not randomized paired confidence intervals, a guaranteed
gain across workloads, or permission to choose only the favorable baseline.
The reboot separates some arms and the baseline itself varied materially.

Cold prefill is essentially unchanged:

| Arm, fresh namespace | ~64K TTFT | One ~490K, all three needles, TTFT |
|---|---:|---:|
| Baseline | 4.969s | 61.070s |
| FR-Spec | 4.886s | 61.319s |
| BF16-only, held | 5.009s | 61.185s |

Server prompt usage is63,864 and489,879 respectively. All successful arms
returned exact READY / all three separated needles. Prefill throughput-to-first
token is approximately12.9–13.1K and8.0Ktok/s; it is not decode throughput.

Sample-level numeric evidence, server usage, per-stream rates, acceptance and
memory observations are preserved in the [machine-readable record](qwen38-flash-next-frspec-20260905.json).
Raw prompts, SSE, journals, operational paths and grading packets remain in
the immutable local evidence. The public numeric record is derived evidence,
not a substitute raw trace. No first attempt or automatic outcome was rewritten.

## Reasoning — full breakdown

Two warmups, nine measured requests in `three-user-1-3-3-1`, with launcher
defaults owning effort and ceiling. All nine ended naturally;131,770 measured
completion tokens, no collector loop events or fatal mechanical caps.

Qualitative **98.52/100**, final **98.52/100**.

| Case | Score /100 | Main qualification |
|---|---:|---|
| C1 | 97.28 | Correct MTU1404; long/repetitive presentation. |
| C2 | 96.74 | Correct causal diagnosis; unnecessary unsupported intermediate-event hypothesis. |
| C3 | 98.91 | Correct6A/5B/4048 optimum and infeasibility argument; repetition. |
| C4 | 100.00 | Correct17 schedule/proof and X/19 consequence. |
| C5 | 96.74 | Correct claim-before-account/idempotency/canonical-locking design; unnecessary impossible rollback branch and length. |
| C6 | 100.00 | Correct no-release decision. |
| C7 | 100.00 | Correct sharp5/14..1 bounds and assumption-only28/37, with endpoint constructions. |
| C8, including correction | 98.50 | Correct X then W; first-turn confidence not explicit. |

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

Case weights:14/12/14/14/16/10/10/10. No fatal35, confirmed-loop20 or
repetitive-exhaustion10 caps applied. Unchanged repository scoring tool used.

Grading method: paired opaque packets from the repository anonymizer;
qualitative files locked and hashed **before** revealing arm mapping and
operational metadata or applying mechanical caps. Parent agent reviewed all
visible answers/correction plus selected reasoning spans, not every token of
both long chains and not an independent external panel. The paired archived
checkpoint control scored97.62 under the same review. Its prompts and omitted
request controls match, but it used an older runtime and sequential execution.
It is contextual quality evidence, **not** a new current-baseline run, a
performance comparator, or proof that FR-Spec improved reasoning quality.

The qualitative lock and original grade files remain in local evidence.
The numeric record preserves the unmodified final case and dimension scores.

Measured reasoning scheduler samples, separated by running count:

| Running requests | Samples | Aggregate tok/s median | Acceptance length median | Acceptance rate median |
|---|---:|---:|---:|---:|
| 1 | 948 | 145.07 | 2.00 | 0.33 |
| 2 | 105 | 277.53 | 2.19 | 0.40 |
| Exactly3 | 128 | 353.94 | 2.13 | 0.38 |

These are logged interval samples grouped by the current scheduler count,
not exact occupancy-duration attribution or time-weighted throughput.
Transition intervals can include prior occupancy. All selected samples report
CUDA graphs true. Complete ranges and provenance are in
qualification-receipts.json (retained local evidence).
Reasoning memory plateau peaked at95,499MiB used /1,793MiB free in sampling;
final idle after concurrent restore95,517MiB used /1,775MiB free.
After the two additional continuation turns:95,537MiB used /1,755MiB free,
zero running/queued requests and unchanged824,384-token capacity.

## Tools, vision and sealed controls

- Tools: **27/30 automatic**, **29/30 exact tools/arguments**,30/30 parseable,
  zero runtime errors; conservative parent semantic assessment28/30 with
  explicit criteria. Not reported as30/30. One invoice answer adds forbidden
  extra prose while rejecting an injection; one deployment answer overclaims
  rollback/blast-radius guarantees. Both invalid-date answers are correct but
  miss the literal checker; one also unnecessarily repeats the read-only call.
  Operationally:29 clean tool workflows, one minor redundant read-only call,
  **no consequential tool execution failure**. Answer-quality caveats and
  literal-match failures are not additional broken tools.
- Vision: automatic and manual spatial/claim-separation check pass,377 tokens,
  natural stop under the current1,024-token fixture cap.
- Sealed agentic: pass, six model turns / exactly five tools, correct revised
  artifact and final inspection.
- Sealed natural decode: exactly3,072 server tokens, all3,072 raw direct IDs,
  no error/tools. Original automatic gate remains false because the collector
  reads `token_ids`, while SGLang returns `response_token_ids`. Separate
  count/hash receipt retained; no result was rewritten to pass.

Full findings and a second collector snapshot-aliasing limitation:
SEMANTIC-REVIEW.md (retained local evidence).
Those collector fixes belong to **jpezzulli/pennyroyal-validation**, deferred
separately. Their source was not changed during this experiment. First attempts
remain intact; no selective rerun replaced a failure. No fresh matching full
baseline tool run establishes whether the behavioral misses are FR-specific.

## NIXL, rollback, isolation and 27B compatibility

FR-Spec wrote fresh namespaces in its initial cold arm, then reused the exact
same FR representation after the intervening BF16/combined/released-baseline
boots. Released baseline restore also worked after removing the candidate
wheel and John's reboot. Thus both released and FR states were revisited;
different arm identities did not share storage namespaces. Source/map guards
and focused map/identity checks passed. No intentional missing-sidecar or
manifest-corruption injection was performed in this campaign; unchanged
released restore-boundary behavior is not re-proven as transactional storage.

| Restarted profile | NIXL64K restored tokens / TTFT | NIXL490K restored tokens / TTFT |
|---|---|---|
| Released Next return | 63,808 /1.193s | 489,856 /6.592s |
| FR-Spec Next | 63,808 /1.213s | 489,856 /5.940s |
| Unchanged27B FP8/DFlash2 | 63,808 /1.804s | 489,856 /11.247s |

All READY/three-needle checks pass. Each individual restored request increments
Mamba load-back by two states; captured backend registration and all-pool byte
counters accompany KV evidence. FR's490K request loaded7,046,561,824 bytes
through the all-pool counter. These are actual storage-hit/load-back deltas,
not just a warm response or device-prefix hit.

Final FR restart: four barrier-submitted requests, two each of the identical
saved64K/490K prompts, completed in **9.396s aggregate makespan**, all correct.
Counter deltas: **553,664 NIXL storage-hit tokens**,553,664 device-hit tokens,
553,664 KV load-back tokens,4 Mamba states,8,067,100,736 all-pool load-back
bytes. The repeated pair reused the now-admitted prefix; do not call this
four independent full disk transfers or four simultaneous GPU prefills.
Original requests, SSE, metrics and journal are in
the retained local evidence and the retained local evidence.

Explicit long-conversation continuation gate, completed after John's follow-up:
the saved490K request and its actual prior assistant answer were extended
with two ordinary user turns. The first temporarily changed ALPHA while
preserving BRAVO/CHARLIE; the second withdrew that override and required the
original archive ALPHA. Both returned the exact expected JSON, natural stop,
no tools:489,984 prompt /106 completion tokens in5.210s, then490,081 prompt /
111 completion tokens in4.791s. This supplements, not replaces, the canonical
suite or any first attempt. Saved requests, raw SSE, responses and cache
counters: the retained local evidence.

27B was booted on its untouched original launcher and released wheel;
**1,118,784 KV**, full graph settings,9/9 smoke,64K/490K,C1 and C4 passed.
Single compatibility sample:C1 post-first106.73tok/s, C4 aggregate363.81tok/s.
No 27B performance improvement is claimed. Its full reasoning/tool campaign
was not repeated because no shared candidate code is installed. This does
**not** qualify the held shared BF16 patch for27B.


## Follow-up gate and final disposition

The initial combined arm's incomplete status above is preserved as its first
attempt. Later standalone sanitizers and direct traces did not reproduce the
hang. A clean, unprofiled six-sample FR-relative A/B then measured C1
173.05→172.13tok/s (−0.53%) and C4 aggregate450.94→451.55tok/s (+0.13%),
with824384 KV tokens in both. No meaningful incremental BF16 gain; that
kernel is not adopted. The earlier hang remains unexplained, not a proven
kernel defect or a fixed driver failure. This follow-up is not folded into
or substituted for the frozen FR/base comparisons above.

The frozen FR-only launcher was restored on the unchanged released wheel.
Final9/9 ordinary smoke and489856-token NIXL restart restore, all three
needles, full capacity and idle scheduler were verified. The source, map,
wheel and all1327 frozen artifact checksums remained intact. No raw local
operational state is published here.

Runtime release, recipes and attribution:
[Pennyroyal 2.3](https://github.com/jpezzulli/sglang-rtxpro6000/releases/tag/pennyroyal-v2.3.0).
