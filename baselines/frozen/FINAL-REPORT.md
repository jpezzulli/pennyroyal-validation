# Clean native mapped-W2/DSpark-3 frozen-suite report

## Conclusion

The clean native candidate shows **no material suite-level quality regression** and **no tool-use regression**:

- Reasoning: **92.66/100** versus **92.76/100** established baseline.
- Tool-use/agent suite: **30/30 reviewed**, matching the **30/30** validated baseline.
- Both suites completed on one uninterrupted stable server instance. There were no OOMs, crashes, parser failures, heat stops, confirmed loops, or length terminations.

The important case-level finding is C5: compared with the perfect baseline answer, this run omitted distinct-account and integer-amount validation and made one incorrect money-conservation statement. C8 correction quality improved, offsetting most of that score loss. C4 was correct but inefficiently self-revisiting.

The candidate’s operational risk remains VRAM headroom: post-capture free VRAM was **1,057 MiB**, reasoning reached **29 MiB**, and the 200 ms tool-suite sampler reached **3 MiB**. This run proves stability for these frozen suites, not soak stability or safety under arbitrary larger dynamic workspaces.

## Frozen identities

- Reasoning suite: `d1397529eedf72b0f80d5c452c378ed15fb10f1122e4fb9b50f69e1074c0e756`
- Reasoning protocol: `56fb8d57dda656495c5b18d5fc6ea35f533bae351d9696cba087fa2913bde928`
- Reasoning rubric: `ea85f50f9c3cce2f9d9b6b63a3611ffd2e14d9cb90dc4a3d7b5bf7dc0f9c1c65`
- Tool suite: `2be4040e75d8f0f70bf472d5a0f686cd92ceb58bc6304db52ca6758797f4e294`

## Preservation and cleanup

Complete requests, streamed/raw responses, reasoning, tool calls and tool results, frozen definitions, grades, telemetry, server metrics, mapped-allocation audit, server log, and Git provenance are preserved in the containing artifact directory. The server was stopped after both suites. RTX PRO 6000 VRAM returned to baseline, mapped host memory was released, and both implementation worktree statuses remained byte-for-byte unchanged from pre-test state.

