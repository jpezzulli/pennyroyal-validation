# Frozen tool-use suite: max reasoning and top-p 0.95

## Result

The unchanged 30-invocation frozen tool/agent suite passed **30/30** using its
frozen automatic evaluator. No manual rescue was required. There were no HTTP
or harness errors, OOMs, retries, loops, parser failures, length terminations,
or runtime instability.

This matches the validated **30/30 reviewed** baseline and improves the
immediately preceding run's automatic result from 29/30 to 30/30. The previous
automatic miss was only an equivalent date-format representation and had been
accepted on review; therefore this is cleaner automatic conformance, not a
newly recovered deployment capability.

The frozen harness hardcoded request-level `reasoning_effort=high`, which would
have overridden the requested launch shape. A preserved one-line execution
overlay changed only that request field to `max`. The original suite definition,
prompts, tool schemas, expected outputs, evaluator logic, ordering, and all
other request fields remained unchanged. The exact diff and both source hashes
are preserved in `tool/provenance`.

## Throughput and DSpark

| Metric | high / top-p 1.0 | max / top-p 0.95 | Change |
|---|---:|---:|---:|
| Automatic passes | 29/30 | 30/30 | +1 automatic conformance |
| Reviewed passes | 30/30 | 30/30 | unchanged |
| Effective completion rate | 41.27 tok/s | 42.46 tok/s | +2.9% |
| Server decode rate | 61.07 tok/s | 60.24 tok/s | -1.4% |
| Server prefill rate | 1,401.16 tok/s | 1,483.93 tok/s | +5.9% |
| Suite wall time | 119.66 s | 131.66 s | +10.0% |
| Completion tokens | 4,938 | 5,591 | +13.2% |
| DSpark acceptance | 67.82% | 62.47% | -5.34 points |
| Mean accepted span | 3.035 | 2.874 | -0.160 tokens |

The 1.4% server-decode difference is within ordinary run-to-run noise and is
not a material regression. Current DSpark position acceptance was 78.66%,
61.65%, and 47.11% for positions 1–3.

## Telemetry

- Host power: 450.93 W average, 563 W peak.
- GPU power: 148.15 W average, 217.71 W peak.
- Combined host plus GPU power: 599.08 W average, 710.74 W peak.
- Peak temperatures: CPU0 61 C, CPU1 63 C, GPU 47 C.
- GPU utilization: 73.53% average, 100% peak.
- PCIe traffic: 11,572 MiB/s RX average, 30,058 MiB/s peak; 2,331 MiB/s TX average, 7,810 MiB/s peak.
- RAM used: 28.47 GiB average, 32.16 GiB peak; RAM available never fell below 187.57 GiB.
- Physical GPU0 free VRAM sampled as low as 3 MiB, matching the known prior minimum and remaining the principal operational risk.

## Scope and interpretation

This result establishes unchanged frozen-suite behavior for the combined
`reasoning_effort=max` and `top_p=0.95` serving shape. It is one stochastic
pass and does not independently attribute behavior to either setting.
