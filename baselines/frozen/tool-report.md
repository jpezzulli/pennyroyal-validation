# Frozen tool-use/agent suite — clean native mapped-W2/DSpark-3

## Result

- **30/30 reviewed passes**, matching the established validated **30/30 baseline**.
- Frozen automatic evaluator: **29/30**. Invocation 10 used the exact `get_order` call and arguments and returned the authoritative ETA as “August 3, 2026”; human review accepted it as semantically identical to `2026-08-03` because the case did not require ISO output formatting.
- Exact tool selection and arguments: **30/30**. Tool arguments parseable: **30/30**.
- No HTTP/harness error, OOM, retry, loop, parser failure, length termination, or runtime instability.

## Covered behavior

- No-tool restraint and exact output.
- Exact tool selection and argument construction.
- Clarification for missing address/date.
- Grounded order lookup.
- Primary-tool error recovery through the specified fallback.
- Untrusted tool output resistance.
- Dependent customer/order calls.
- Invalid-input validation without unauthorized action.
- One-shot restart control.
- Exact JSON and arithmetic.
- Two delegated analyses and synthesis.
- Long-context retrieval and exact verification call.
- Three concurrent main/subagent requests.

## Runtime and throughput

- 30 invocations completed in **119.657 s**.
- API completion tokens: **4,938**; aggregate effective completion rate: **41.27 tok/s**.
- Server prefill: **66,009 tokens / 47.110 s = 1,401.16 tok/s**.
- Server decode: **4,938 tokens / 80.860 s = 61.07 tok/s**.
- DSpark: **3,300 / 4,866 drafted tokens accepted = 67.82%**; mean accepted span **3.035 tokens/step**. Position acceptance: **82.31%, 67.39%, 53.76%**.

## Power, thermal, memory, and PCIe

- Host power: **469.08 W average, 578 W peak**. GPU power: **141.68 W average, 212.61 W peak**. Samplewise host+GPU: **610.76 W average, 727.37 W peak**.
- Peak temperatures: CPU packages **55°C / 67°C**; GPU **45°C**.
- PCIe RX: **10,130 MiB/s average, 30,159 MiB/s peak**. PCIe TX: **2,232 MiB/s average, 6,907 MiB/s peak**.
- Minimum direct physical free VRAM sample: **3 MiB**. The full suite remained stable, but this is extremely narrow operating headroom and remains a deployment risk.

## Baseline comparison

The candidate matches the established validated 30/30 capability baseline and improves on the separately preserved 26/30 DSpark-175 run. No tool-capability regression was observed.

