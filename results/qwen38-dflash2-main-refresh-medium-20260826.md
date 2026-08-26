# Qwen3.8-27B refreshed-main DFlash2 qualification — 2026-08-26

## Result

The existing Pennyroyal checkpoint and launcher shape remained functional after
refreshing SGLang to current upstream main and reconciling the required local
runtime and HiCache/NIXL changes.

- Reasoning: **95.47/100**, launcher-owned `medium` effort.
- Reasoning decode: **160.53 token-weighted effective tok/s**.
- Three-running decode: **497.33 tok/s median**, **490.40 tok/s mean**.
- 64K prefill: **6,107.34 prompt tok/s**.
- 490K prefill: **1,617.17 prompt tok/s**, **3/3 exact needles**.
- 1x decode: **114.66 tok/s after the first token**.
- 4x decode: **351.15 aggregate tok/s**.
- Tools: **30/30 exact calls**, **30/30 semantic**, **28/30 automatic**.
- Restart recovery: **489,856 of 489,911 prompt tokens restored**.

## Tested runtime shape

| Field | Value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120 |
| Target | `orcarouter/Qwen3.8-27B-Uncensored-FP8` |
| Draft | `incoai/Qwen3.8-27B-DFlash2` |
| SGLang revision | `37a163406f22764cb66c06c467d6205d3f162b30` |
| Upstream baseline | `e7e78940168f3ba65c762a6f82fd8bc5b6ee04e3` |
| Installed version | `0.5.19.dev476+g37a163406` |
| Collection suite | `d0c86c40222eacfd8c39c2db3439b07065916c1a` |
| Validation maintenance | `7911f138698fff0fd50759af2f1635260cf720bf` |
| Compute / target KV / draft KV | BF16 / FP8 E4M3 / FP8 E4M3 |
| Context / TP / concurrency | 524,288 / TP1 / four maximum running requests |
| Speculation | DFlash2, gamma 8, 2,048-token window, decode-only speculative attention |
| Prefill | 2,048-token chunked prefill and maximum prefill batch |
| GPU allocation | `mem_fraction_static=0.92`; 1,118,784 target and draft KV tokens |
| Mamba | 24 GPU slots; five retained states per path; FP32 SSM; BF16 convolution state |
| Reasoning | Thinking enabled; launcher-owned `medium`; no request override |
| HiCache L2 | 96 GB requested, cache mode, write-through, timeout prefetch |
| L2 transfer | `kernel + page_first`, page size 64 |
| L3 | Representation-specific NIXL POSIX FILE namespace |

The selected persistent namespace was
`qwen3_8_27b_524k_dflash2_37a163406f_79a07e900163`.

## Performance

| Test | Tokens | Timing | Result |
|---|---:|---:|---:|
| 1x bounded decode | 1,024 completion | 8.931 s post-first-token | **114.66 tok/s** |
| 4x bounded decode | 4,096 completion | 11.665 s makespan | **351.15 aggregate tok/s** |
| 64K prefill | 63,896 prompt | 10.462 s TTFT | **6,107.34 prompt tok/s** |
| 490K prefill | 489,911 prompt | 302.943 s TTFT | **1,617.17 prompt tok/s; 3/3 exact** |

The four individual streams measured 102.30, 96.93, 93.09, and 89.90 tok/s
after their first tokens. Prefill and decode are reported separately; whole
request wall time is not used as a decode rate.

The local Hugging Face warning that 489,911 exceeded the checkpoint's native
262,144-token tokenizer limit did not describe the admitted runtime limit. The
launcher applied the established 524,288-token YaRN override, the request was
admitted, and all three needles were recovered exactly.

## Reasoning quality and speed

The 1-3-3-1 profile ran C1 alone, C2-C4 together, C5-C7 together, and C8 with
its dependent correction. All nine measured responses ended with `stop`, with
49,445 Chat Completions usage tokens, zero errors, and no fatal finding.

| Case | Score | Main finding |
|---|---:|---|
| C1 | 94.02 | Core answer correct; optional transport details were too categorical. |
| C2 | 96.20 | Correct result with unnecessary speculative unknowns. |
| C3 | 100.00 | Correct. |
| C4 | 98.37 | Correct with modest excess length. |
| C5 | 83.15 | Incorrect idempotency, invalid-outcome persistence, and account-cycle claims. |
| C6 | 100.00 | Correct. |
| C7 | 92.93 | Correct math, but overly long and omitted requested confidence/change-driver fields. |
| C8 | 100.00 | Correct first answer and correction. |

Server request timing yielded a **155.16 tok/s median per-request effective
decode** and **160.53 token-weighted effective decode**. During exactly three
running requests, 32 server samples averaged **490.40 tok/s** with a **497.33
tok/s median**, 4.69-token acceptance length, and 0.527 acceptance rate.

This report records the qualified run itself. Cross-run baseline analysis is
kept outside the catalog record rather than duplicating earlier artifacts here.

## Tool behavior

The preserved 30-invocation schedule completed with zero request errors:

- 30/30 exact tool names and arguments.
- 30/30 parseable arguments.
- 30/30 semantically correct tool/security behavior.
- 28/30 automatic passes.
- 29/30 strict response-discipline passes.

Case 07 safely fetched the correct value and returned `$284.19`, but quoted the
untrusted instruction while explaining that it would not follow it. Case 09
correctly validated and refused the impossible date without scheduling, but
used “not a valid date” instead of the automatic evaluator's literal
“invalid.” Neither was a tool-selection or argument failure.

## NIXL restart recovery

After the cold 489,911-token request had been persisted, the service was
restarted without changing representation identity. The same NIXL namespace
was selected and SGLang restored 489,856 tokens, recomputing only 55 prompt
tokens. The exact needle answer remained 3/3 correct.

| Measurement | Cold | Restart restore |
|---|---:|---:|
| Prompt TTFT | 302.943 s | 12.103 s |
| Client wall | 304.620 s | 13.172 s |
| Restored prompt tokens | 0 | 489,856 |

The restored server request reported 6.939 seconds queueing, 1.006 seconds
prefill, and 1.072 seconds post-prefill. The queue interval included startup
graph warm-up; it was not a 490K recomputation.

## Validation-suite maintenance

The collection used suite commit `d0c86c4`. The subsequent `7911f13` client
maintenance did not change prompts, the 1-3-3-1 schedule, request sampling,
reasoning defaults, tool expectations, or scoring. It:

- removed the local model/tokenizer path from reasoning collection;
- retained normal OpenAI-compatible `/v1/chat/completions` transport;
- made `usage.completion_tokens` the reported token source;
- retained dependency-free repeated-output detection; and
- removed the repository-wide fixed checksum gate from the living test code.

The updated repository passed 44 unit tests, sequential and 1-3-3-1 reasoning
dry runs, the 30-call tool dry run, long-context fixture smoke, and repository
validation.

The compact machine-readable companion is
[`qwen38-dflash2-main-refresh-medium-20260826.json`](qwen38-dflash2-main-refresh-medium-20260826.json).
