# Frozen reasoning suite — clean native mapped-W2/DSpark-3

## Result

- Locked qualitative score: **92.66/100**.
- Established 175-slot baseline: **92.76/100**; delta **-0.10 point**, not a material suite-level regression.
- All nine measured requests finished with `stop`; no HTTP error, OOM, heat stop, length exhaustion, or operational loop event.
- C1, C2, C3, C6, and C7 were fully correct. C4 reached the correct schedule and proof but its hidden reasoning repeatedly revisited branches. C5 missed rejection of identical account IDs and integer validation and misstated the effect of a negative transfer. C8 repeated the baseline first-turn containment error, then correctly and explicitly retracted it on correction.
- No fatal-condition cap applied.

## Runtime and throughput

- Exact candidate: Runner V2, DSpark-3, mapped canonical W2 layers 40–42 on NUMA node 0, 512 FP4 correction slots / 6 GiB, `gpu_memory_utilization=0.988`, FP8 MLA KV, normal CUDA graphs.
- Runtime-reported KV capacity: **625,757 tokens**; configured context: **393,216 tokens**. This suite did not exercise that full context.
- Post-capture physical free VRAM: **1,057 MiB**; minimum observed during reasoning: **29 MiB**.
- Measured wall time: **529.739 s**; local generated tokens: **28,326**; effective local rate: **53.47 tok/s**.
- Server decode: **28,928 tokens / 515.259 s = 56.14 tok/s**. Server prefill: **5,310 tokens / 34.475 s = 154.02 tok/s**.
- DSpark: **16,998 / 35,781 drafted tokens accepted = 47.51%**; mean accepted span **2.425 tokens/step**. Position acceptance: **68.11%, 44.93%, 29.47%**.

## Power, thermal, and I/O evidence

- Host power: **444.32 W average, 572 W peak**. GPU power: **146.97 W average, 158.71 W peak**. Samplewise host+GPU: **591.29 W average, 722.79 W peak**.
- Peak temperatures: CPU packages **55°C / 62°C**; GPU **43°C**.
- Peak PCIe RX/TX samples: **28,049 / 6,213 MiB/s**.
- No unsafe thermal condition occurred.

## Comparison qualification

The quality comparison is exact-suite and exact-rubric. Performance is not fully workload-matched because generation length was model-controlled; notably C4 generated 15,818 local tokens and consumed 299.44 seconds. The server decode rate is consistent with the mapped-host bounded result near 55 tok/s.

