# Clean native mapped-W2/DSpark-3 max/top-p validation

## Conclusion

The requested launch shape improved reasoning quality without a material
throughput or tool-use regression:

- Frozen reasoning suite: **96.86/100**, versus **92.66/100** in the immediate
  high/top-p-1.0 comparison and **92.76/100** in the established baseline.
- Frozen tool/agent suite: **30/30 automatic and reviewed**, matching the
  validated 30/30 deployment baseline.
- Reasoning server decode was 58.44 tok/s versus 56.14 tok/s; tool server
  decode was 60.24 tok/s versus 61.07 tok/s. The latter -1.4% is normal noise,
  not a material speed regression.
- No OOM, crash, loop, retry, parser failure, truncation, heat stop, or runtime
  instability occurred across either suite on the shared server instance.

The quality result should be attributed only to the combined launcher-level
`reasoning_effort=max` and `top_p=0.95` shape. Startup confirms that DeepGEMM
was enabled, but the prior comparison run already selected the same DeepGEMM
FP8 and MXFP4 kernels. It was therefore controlled, not a new speed variable.

## Exact candidate shape

The model/runtime candidate was unchanged: Runner V2, DSpark-3, canonical W2
layers 40–42 mapped to NUMA node 0 pinned host memory, 512 FP4 correction slots
(6 GiB), normal CUDA graphs, FP8 MLA KV, `gpu_memory_utilization=0.988`, and
configured context 393,216 tokens. Startup again reported 625,757-token KV
capacity, 1,057 MiB physical free VRAM after graph capture, exactly
5,435,817,984 mapped W2 bytes, and zero redundant complete GPU W2 copies.
Configured or capacity token counts are not exercised-context results.

## Frozen identities and request change

- Reasoning suite: `d1397529eedf72b0f80d5c452c378ed15fb10f1122e4fb9b50f69e1074c0e756`
- Reasoning rubric: `ea85f50f9c3cce2f9d9b6b63a3611ffd2e14d9cb90dc4a3d7b5bf7dc0f9c1c65`
- Original tool suite: `2be4040e75d8f0f70bf472d5a0f686cd92ceb58bc6304db52ca6758797f4e294`
- Tool execution overlay: `77d5624692e928003500eb1c729bb61ec7aafad6dc0359631d6dca4b25df4299`

The tool overlay changed only its hardcoded request field from
`reasoning_effort=high` to `reasoning_effort=max`; otherwise the frozen suite
and evaluator remained intact. The reasoning harness already inherited the
launcher-level setting and required no alteration.

## Preservation and caveats

Complete raw and streamed responses, reasoning content, tool calls/results,
grades, telemetry, server counters, suite definitions, hashes, request-overlay
diff, mapped-allocation audit, runtime configuration, and server logs are
preserved in this artifact directory.

The server was stopped after both suites; GPU0 returned to 1 MiB used and no
process remained on port 8001. The tool run again reached a sampled 3 MiB of
physical free VRAM. This run proves suite stability, not arbitrary-workload or
soak headroom.

Source status changed concurrently between the pre-test snapshot and final
verification in paths unrelated to the request-only max/top-p test. Those
exact pre/post snapshots and their diff are preserved; this test did not edit
runtime source or implementation files, and no attempt was made to overwrite
the externally changed state.
