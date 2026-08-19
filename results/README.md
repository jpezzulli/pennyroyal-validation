# Curated model-run history

This history records selected configurations, completed qualifications,
materially different model/runtime paths, and failed configurations that
established useful boundaries. It is not a leaderboard, and rows are not
normalized into an artificial comparison.

The exact machine-readable fields, evidence roots, unknowns, and warnings are
in [`runs.json`](runs.json). Large inspectable bundles are published as
release assets and indexed in [`assets.json`](assets.json).

| Date | Model and runtime | Outcome | Headline evidence |
|---|---|---|---|
| 2026-07-31 | DeepSeek-V4-Flash 0731, vLLM-MoET | Selected historical base | 87.54/100 after frozen fatal caps; 30/30 reviewed tools in later mapped-W2 passes; durable C5 weakness retained |
| 2026-08-02 | DeepSeek-V4-Flash 0731, Runner V2 mapped-W2 DSpark-4 | Selected | 97.07/100; 30/30 exact tools; 994,987-token retrieval; 1,000,000-token admission |
| 2026-08-10 | Ling 3.0 Flash NVFP4, repaired stock-derived vLLM | Rejected boundary | 73.80/100 after fatal caps; 30/30 semantic tools; material C4/C5 reliability failures |
| 2026-08-14 | SehyO Qwen3.5-122B, stock vLLM | Selected then superseded | 490,002-token 3/3 retrieval at 1,986 tok/s; 150.46 tok/s 1x decode under an earlier launch shape |
| 2026-08-15 | Qwen3.8-27B BF16, stock vLLM | Qualified candidate | 97.34/100; 29/31 semantic tools; 1,783.64 tok/s near-490K prefill; 55.29 tok/s natural 1x |
| 2026-08-15 | Qwen3.8-27B official FP8 with BF16 KV, stock vLLM | Clean pre-Ferrari reference | 96.96/100; 31/31 tools; 6,753.58 tok/s 64K prefill; 2,280.13 tok/s near-490K prefill |
| 2026-08-15 | Qwen3.8-27B MTP NVFP4, stock vLLM | Rejected boundary | 87.96 final reasoning; 30/31 tools; repeatable material C5 idempotency failure |
| 2026-08-16 | Qwen3.8-27B Uncensored FP8, Ferrari vLLM | Selected then superseded | 97.34/100; 30/31 semantic tools; 100.24 tok/s natural 1x; 299.52 tok/s four-way |
| 2026-08-17 | Qwen3.8-27B Uncensored FP8, native SGLang DSpARK | Selected then superseded | 98.35/100; 30/30 exact tools; 7,425 tok/s 64K prefill; 342.72 tok/s four-way |
| 2026-08-18 | Qwen3.8-27B Uncensored FP8, native custom SGLang DFlash2 | Current selected | 98.56/100; 28/30 automatic tools; 30/30 exact calls; 125.8 tok/s reasoning decode; zero failures/truncations |

## Current DFlash2 qualification

The current selected run used:

- target: `orcarouter/Qwen3.8-27B-Uncensored-FP8`;
- native custom SGLang on one RTX PRO 6000 Blackwell;
- source commit `6a2c055eff9fd66f7df100c22a9c50dbf1336fda`;
- DFlash2 with an independent
  `incoai-Qwen3.8-27B-DFlash2` draft;
- FP8 E4M3 target and draft KV;
- 524,288-token admission and 1,194,496-token shared KV capacity.

Reasoning scored 98.56/100 and generated 182,963 completion tokens at
125.8 engine-decode tok/s. DFlash accepted 3.36 tokens per step. The tool suite
reached 158.3 engine-decode tok/s and 132.0 wall tok/s, scored 28/30
automatically, and achieved 30/30 exact tool selection and arguments. Prefill
was 6,659 tok/s at 64K and 1,755 tok/s at 455K. Bounded decode was 92.9 tok/s
for one 1,024-token request and 324.6 tok/s aggregate for four requests. No
request failed or truncated.

The earlier recorded DSpARK prefill results used BF16 target KV. DFlash2 used
FP8 target KV. Their prefill difference therefore does not establish a drafter
difference.

## Included and excluded evidence

Included runs meet at least one curation rule: completed qualification,
selection, material model/runtime/format change, or durable failure boundary.
The registry excludes ordinary gamma/K sweeps, cache and graph warm-ups,
repeated control attempts, short-lived power/clock experiments, partial
retries, invalid benchmark shapes, and other intermediate tuning that did not
establish a reusable boundary.

Raw local archives were not deleted, moved, or rewritten. Git contains compact
summaries and manifests; release assets contain selected detailed material.
When a historical raw root could not be recovered from the archive, the run
entry says so rather than inventing a path or precision.
