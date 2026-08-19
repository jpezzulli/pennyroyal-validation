# Results

Runs are listed newest first. Each row describes the model and runtime that was
actually tested; it is not a ranking or a recommendation. Different suite
versions, context sizes, KV formats, and speculative methods are left visible
instead of being normalized into an artificial comparison.

## How to read the table

- `R`: reasoning generation speed.
- `T`: tool-suite generation speed.
- `1x`: single-request decode speed.
- `4x`: aggregate decode speed across four simultaneous requests.
- All speed values are tokens per second.
- A dash means the measurement was not captured, not that the result was zero.
- Tool denominators differ because the runs used different frozen suite versions.

## Runs

| Date | Model and runtime | Reasoning | Tools | Measured speed |
|---|---|---:|---:|---|
| 2026-08-18 | Qwen3.8-27B Uncensored FP8 · SGLang DFlash2 | 98.56/100 | 28/30 automatic; 30/30 exact calls | R 125.8; T 132.0 wall / 158.3 engine; 1x 92.9; 4x 324.6; 64K prefill 6,659; 455K prefill 1,755 |
| 2026-08-17 | Qwen3.8-27B Uncensored FP8 · SGLang DSpARK | 98.35/100 | 26/30 automatic; 29/30 semantic; 30/30 exact calls | R 105.8; 1x 88.81; 4x 342.72; 64K prefill 7,425; 455K prefill 2,161 |
| 2026-08-16 | Qwen3.8-27B Uncensored FP8 · Ferrari vLLM | 97.34/100 | 26/31 automatic; 30/31 semantic | R 71.67; 1x 100.24; 4x 299.52; 64K prefill 6,773.28; 490K prefill 2,269.94 |
| 2026-08-15 | Qwen3.8-27B MTP NVFP4 · stock vLLM | 87.96/100 | 30/31 semantic | 1x 88.39; 64K prefill 8,300.16; 490K prefill 2,238.72 |
| 2026-08-15 | Qwen3.8-27B FP8 with BF16 KV · stock vLLM | 96.96/100 | 31/31 semantic and exact | 1x 74.06; 64K prefill 6,753.58; 490K prefill 2,280.13 |
| 2026-08-15 | Qwen3.8-27B BF16 · stock vLLM | 97.34/100 | 27/31 automatic; 29/31 semantic | 1x 55.29; 4x 215.81; 64K prefill 4,843.93; 490K prefill 1,783.64 |
| 2026-08-14 | SehyO Qwen3.5-122B · stock vLLM | — | — | 1x 150.46; 4x 461.62; 490K prefill 1,986 |
| 2026-08-10 | Ling 3.0 Flash NVFP4 · vLLM | 73.80/100 | 26/30 automatic; 30/30 semantic and exact | R 70.8; 512-token decode 69.9; 16K prefill 5,994 |
| 2026-08-02 | DeepSeek-V4-Flash 0731 · mapped-W2 DSpark-4 | 97.07/100 | 30/30 automatic and exact | R 54.92 wall; T 40.36 wall; 995K prefill 1,024.18 |
| 2026-07-31 | DeepSeek-V4-Flash 0731 · vLLM-MoET | 87.54/100 | 30/30 reviewed in later mapped-W2 passes | R 39.78 wall |

## 2026-08-18 DFlash2 details

- Model: `orcarouter/Qwen3.8-27B-Uncensored-FP8`
- Runtime: custom SGLang on one NVIDIA RTX PRO 6000 Blackwell
- Speculation: DFlash2 with an independent Qwen3.8-27B draft
- Target and draft KV: FP8 E4M3
- Context admitted: 524,288 tokens
- Shared KV capacity: 1,194,496 tokens
- Reasoning: 98.56/100 across 182,963 completion tokens
- Tool calls: 30/30 exact names and arguments
- Failures or truncations: zero

DFlash2 accepted 3.36 draft tokens per step. Reasoning generation ran at 125.8
tokens/s. The tool suite ran at 158.3 engine tokens/s and 132.0 wall tokens/s.
Single-request 1,024-token decode measured 92.9 tokens/s; four-request aggregate
decode measured 324.6 tokens/s.

The DSpARK prefill run used BF16 target KV, while DFlash2 used FP8 target KV.
The prefill difference between those rows therefore does not isolate the
speculative method.

## Evidence and downloads

- [`runs.json`](runs.json) contains the complete machine-readable run records,
  including hardware, context, KV format, runtime revision, and known gaps.
- [`assets.json`](assets.json) maps runs to downloadable evidence bundles and
  records their SHA-256 checksums.
- The [public baseline release](https://github.com/jpezzulli/pennyroyal-validation/releases/tag/public-baseline-2026-08-18)
  contains the detailed result bundles.

The table includes completed qualifications and materially different
model/runtime configurations. Routine tuning sweeps, warm-ups, retries, and
partial experiments are intentionally omitted.
