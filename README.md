# Pennyroyal validation

This private repository preserves the exact reusable validation assets used for
the Pennyroyal DeepSeek-V4-Flash-0731 service on `thegrid`. The scripts, prompts,
tool schemas, expected behavior, rubric, and production request overlay were
copied byte-for-byte from the sealed 2026-08-02 evidence. Do not edit a frozen
suite in place; create a new version if the test contract changes.

## Suites

### Tool-free reasoning

`reasoning/` contains eight difficult cases plus the fixed C8 correction turn.
The measured pass is nine requests after two warm-ups. It measures correctness,
evidence discipline, contradiction detection, constraint preservation,
technical reasoning, unsupported assumptions, confidence calibration, revision
quality, loop behavior, and final-answer usability.

Read `reasoning/design/protocol.md` and `reasoning/design/rubric.json` before
running it. The collector sends no tools and allows up to 65,536 output tokens
for every measured reasoning case. The ceiling was raised from 32K after a
Qwen3.8-27B C5 run exhausted that budget before completing; historical 32K
baselines remain preserved as results under the earlier contract. Qualitative
grading must be locked from the anonymized packet before operational metadata
is revealed.

```bash
run=/opt/ai-artifacts/logs/reasoning-quality-NEW-RUN
mkdir -p "$run/raw" "$run/provenance" "$run/anonymized"
python reasoning/bin/monitor.py "$run/metrics.csv" \
  --interval 1 --heat-sentinel "$run/HEAT_STOP" --cpu-limit 85 --gpu-limit 80
python reasoning/bin/run_suite.py \
  --suite reasoning/design/suite.py --output "$run" \
  --runtime candidate-name --base http://127.0.0.1:8001 \
  --model pennyroyal --heat-sentinel "$run/HEAT_STOP" \
  --tokenizer-path /srv/models/hf/ds4flash0731
python reasoning/bin/anonymize.py \
  --suite reasoning/design/suite.py --results "$run/results.jsonl" \
  --output "$run/anonymized/packet.json"
```

For a targeted confirmation rerun after a clipped case, use a fresh output
directory and add `--case C5` (or another exact case ID) to `run_suite.py`.
Targeted runs skip warm-ups and do not replace the preserved original response.

### Tool use and agent behavior

`tools/suite/` contains the canonical 31-invocation suite: direct answers, exact
tool selection and arguments, clarification, dependent calls, tool-error
recovery, untrusted tool output, invalid input, one-shot action control, exact
JSON, arithmetic, subagent synthesis, long-context retrieval, and a concurrent
main-agent/two-subagent group. The 31st invocation is a generic synthetic
deferred-bridge regression covering `tool_search → tool_describe → tool_call`,
open nested arguments, exact JSON, containment, and parser finalization. It is
self-contained and uses only local canned tool results.

The frozen profile uses `reasoning_effort=high`. The production profile is the
exact one-line overlay in `tools/profiles/production-max.py`, which uses
`reasoning_effort=max`; its diff is preserved beside it. The launcher supplies
`top_p=0.95` for the production profile.

```bash
run=/opt/ai-artifacts/logs/tool-agent-NEW-RUN
deadline=$(( $(date +%s) + 14400 ))
python tools/suite/monitor.py "$run/telemetry.csv" --interval 1 &
python tools/profiles/production-max.py \
  --runtime candidate-name --output-dir "$run" --deadline "$deadline"
python tools/suite/summarize.py "$run"
```

A pass for the canonical suite is reviewed `31/31`, with exact argument,
JSON/DSML, clarification, recovery, invalid-input, synthetic deferred-bridge,
and one-shot behavior intact. The preserved historical production baseline
remains a reviewed `30/30` result from before the synthetic case was added.

### Performance

`performance/decode-1024-harness.py` is the exact sealed client for the bounded
1,024-output-token decode. `performance/run_performance.py` is the exact client
used for target-only single decode, three-way concurrent decode, 64K prefill,
and immediate prefix-cache reuse. These files retain their historical request
settings and output assumptions; copy a client into a new artifact directory
before changing only its output destination.

## Requirements

- An OpenAI-compatible endpoint at `http://127.0.0.1:8001`
- Served model name `pennyroyal`
- Python 3; the 2026-08-02 environment used Python 3.14.6
- `transformers==5.14.1` for reasoning token counting and loop detection
- Standard Linux telemetry interfaces, `sensors`, and `nvidia-smi`
- No candidate-facing tools for the reasoning suite

The launcher controls model/runtime geometry and default sampling except for the
explicit request fields already frozen in a suite/profile.

## Production baseline

- Runtime source: `jpezzulli/vllm:production/pennyroyal-ds4flash-6gib-fp4`
- Validated source commit: `98cef19a50765148aba29084dc88da5d16f31700`
- Exact 1,024-token clean reproduction: 53.83 tok/s
- Sealed 1,024-token reference: 55.02 tok/s
- Frozen reasoning (`reasoning_effort=high`): 92.66/100
- Production reasoning (`reasoning_effort=max`, `top_p=0.95`): 96.86/100
- Frozen and production tool results: 30/30 reviewed

Compact reports are under `baselines/`. Full requests, responses, reasoning,
tool calls/results, server logs, and telemetry remain outside Git under
`/opt/ai-artifacts`; see `docs/artifact-index.md`.

## Integrity

Run `sha256sum -c SHA256SUMS` from the repository root before every campaign.
Generated result directories, logs, environments, model files, and credentials
must never be committed.
