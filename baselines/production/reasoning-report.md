# Frozen reasoning suite: max reasoning and top-p 0.95

## Result

The unchanged nine-request frozen reasoning suite scored **96.86/100** with
no fatal findings. This is **+4.20 points** versus the immediately preceding
clean-native run at launcher `reasoning_effort=high` and model-default
`top_p=1.0` (92.66), and **+4.10 points** versus the established 175-slot
baseline (92.76).

All nine measured responses finished normally. There were no request errors,
loops, length terminations, OOMs, heat stops, or runtime instability.

The strongest qualitative change was C8: the first turn selected X correctly,
and the correction explicitly retracted both the earlier ambiguity and X
before selecting W. C5 was materially stronger than the immediately preceding
run: it rejected self-transfers, handled missing accounts, persisted the
insufficient-funds outcome, compared request fingerprints, used canonical
dual-account locks, and relied on transaction rollback after a uniqueness
conflict. Its remaining deductions were failure to persist every invalid
outcome by request ID, checking positivity without explicitly requiring integer
cents, and one missing-row behavior assumption not specified by the packet.
C4 remained correct and no longer repeated the prior branch-cycling pattern,
although its reasoning was still longer than necessary.

## Runtime and throughput

The actual serving shape included launcher-level
`reasoning_effort=max`, launcher-level `top_p=0.95`, and
`VLLM_USE_DEEP_GEMM=1`. Startup confirmed effective sampling parameters
`temperature=1.0` and `top_p=0.95`, selected
`DeepGemmFp8BlockScaledMMKernel`, and selected `DEEPGEMM_MXFP4`.
DeepGEMM was already active in the comparison run, so it is not a newly
introduced backend and cannot explain the quality difference.

| Metric | high / top-p 1.0 | max / top-p 0.95 | Change |
|---|---:|---:|---:|
| Qualitative score | 92.66 | 96.86 | +4.20 points |
| Effective locally counted output rate | 53.47 tok/s | 57.17 tok/s | +6.9% |
| Server decode rate | 56.14 tok/s | 58.44 tok/s | +4.1% |
| Measured-suite wall time | 529.74 s | 619.31 s | +16.9% |
| Locally counted generated tokens | 28,326 | 35,408 | +25.0% |
| DSpark acceptance | 47.51% | 51.48% | +3.97 points |
| Mean accepted span | 2.425 | 2.544 | +0.119 tokens |

The longer wall time reflects substantially more generated reasoning, not a
decode-rate loss. Current DSpark position acceptance was 71.84%, 49.69%, and
32.90% for positions 1–3.

## Telemetry

- Host power: 458.12 W average, 572 W peak.
- GPU power: 148.60 W average, 169.75 W peak.
- Combined host plus GPU power: 606.72 W average, 724.62 W peak.
- Peak temperatures: CPU0 61 C, CPU1 65 C, GPU 43 C.
- Peak PCIe traffic: 27,417 MiB/s RX and 6,201 MiB/s TX.
- Peak RAM used: 32.69 GiB; peak swap used: 41.65 GiB.

## Scope and interpretation

The suite, rubric, expected answers, response cap, request order, and grading
rules were unchanged. Grading was blinded to operational token counts, timing,
and loop metadata. This is one stochastic pass in which `reasoning_effort` and
`top_p` changed together; it supports the combined launch shape but does not
isolate the causal contribution of either setting.
