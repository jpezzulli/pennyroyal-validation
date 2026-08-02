# Sealed artifact index

Large and raw evidence remains on `thegrid` under `/opt/ai-artifacts`.

| Evidence | Path |
|---|---|
| Clean native startup, structure, arithmetic, and 1,024-token decode | `/opt/ai-artifacts/logs/moet-mapped-w2-clean-validation-20260802-005954` |
| Frozen reasoning and tool suites | `/opt/ai-artifacts/logs/clean-native-mapped-w2-frozen-suites-20260802-060854` |
| Production max/top-p reasoning and tool suites | `/opt/ai-artifacts/logs/clean-native-mapped-w2-max-top095-deepgemm-20260802-064459` |
| Original direct-API reasoning method | `/opt/ai-artifacts/ai-testing-method` |
| Preserved frozen tool suite and older baseline | `/opt/ai-artifacts/logs/tool-agent-frozen-20260801-dspark175` |
| Target-only and prefix-cache performance run | `/opt/ai-artifacts/logs/moet-runnerv2-nomtp-delta512-20260801-203723` |

Configured admission and runtime-reported KV capacity are not exercised-context
results. The archived evidence does not prove soak, tensor parallelism,
other-GPU, other-checkpoint, or full-context behavior.

