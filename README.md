# Pennyroyal model validation

**A practical test suite for the Pennyroyal model and other local language
models.**

Point the validation suite at an OpenAI-compatible model server to find out
whether the served model and runtime can reason through difficult problems, use
tools correctly, follow multi-step agent workflows, retrieve information from
long contexts, and sustain useful generation speed.

The suite saves the requests, responses, scores, and timing data needed to
inspect a result instead of reducing everything to a single benchmark number.
This repository is a record of tested model configurations, not a leaderboard.
Results from different models, runtimes, context sizes, and request shapes are
shown as they were measured and should not be treated as perfectly comparable.

## Run it with Codex, Claude Code, or another coding agent

Give a shell-capable coding agent this exact instruction:

> Read <https://github.com/jpezzulli/pennyroyal-validation/blob/main/RUN_WITH_AI.md>
> and follow it exactly. Prepare and inspect only—do not start inference. When
> preparation is complete, give me the readiness report required by the guide
> and wait for me to choose which suite to run.

The guide tells the agent how to obtain the repository, inspect the frozen
cases, run the safe checks, verify the endpoint, and report whether it is ready.
It works with Codex, Claude Code, and other coding agents that can read files
and run shell commands.

## Reasoning cases

The reasoning suite contains eight cases and one fixed correction turn. Each
case is designed to catch an answer that sounds convincing but violates an
important fact, constraint, or proof obligation.

| Case | What the model must do | Why it is hard |
|---|---|---|
| [C1: Tunnel latency](docs/cases/reasoning.md#c1-tunnel-latency-diagnosis) | Diagnose a path-MTU black hole, calculate the exact packet boundary, and propose the smallest fix. | The evidence comes from different capture points and includes several plausible but irrelevant symptoms. |
| [C2: Event ordering](docs/cases/reasoning.md#c2-authoritative-ordering-versus-client-logs) | Decide what caused an alarm using signed sequence numbers, workstation logs, UI state, and SIEM receipt times. | Wall clocks and observer logs conflict; the model must identify which source is authoritative and preserve what remains unknown. |
| [C3: Production optimization](docs/cases/reasoning.md#c3-production-optimization-with-grade-mix) | Find the cheapest whole-batch production plan that satisfies quantity, grade, energy, and capacity constraints. | Several plans look feasible until every constraint is calculated, and the optimum and reduced-capacity impossibility must both be proved. |
| [C4: Scheduling](docs/cases/reasoning.md#c4-constrained-non-preemptive-schedule) | Build an optimal schedule with two resources, precedence, maintenance, release times, deadlines, and an optional job. | A feasible schedule is not enough; the model must prove the earliest possible finish and correctly reject the tempting optional work. |
| [C5: Idempotent transfers](docs/cases/reasoning.md#c5-idempotent-transfer-implementation-review) | Review a concurrent money-transfer implementation and give a safe transaction and locking design. | Superficial fixes miss duplicate races, request fingerprints, missing rows, durable failure results, lock order, or deadlock handling. |
| [C6: Release decision](docs/cases/reasoning.md#c6-release-decision-with-distractions) | Decide whether a manufacturing lot may ship under exact evidence and waiver rules. | Urgency, a manager note, prior lot history, and a truncated display all encourage an unsafe exception that the rules do not allow. |
| [C7: Probability bounds](docs/cases/reasoning.md#c7-posterior-probability-without-independence) | Calculate the sharp posterior range when only marginal conditional rates are known. | Multiplying the rates gives a neat answer but silently assumes independence; the exact posterior is not identified. |
| [C8: Correcting a decision](docs/cases/reasoning.md#c8-fixed-multi-turn-correction) | Recalculate a decision after one piece of evidence is corrected, retract the old action, and retain unaffected facts. | Models often patch or defend the first answer instead of explicitly revising it without changing unrelated evidence. |

The full case document includes the prompts, expected reasoning, scoring
dimensions, genuine failure conditions, and known evaluator limitations.

## Tool and agent cases

These cases test whether the model chooses the right action, sends the exact
arguments, uses returned data, and stops at the right time. The tools are local
deterministic fixtures: no real weather, customer, order, delivery, or restart
service is contacted.

| Case | What happens | What makes it a useful test |
|---|---|---|
| [01: No unnecessary tool](docs/cases/tools.md#01_no_tool_exact) | Answer `Paris` and do not call the available weather tool. | Tests restraint and exact-output compliance. |
| [02: Obvious weather call](docs/cases/tools.md#02_obvious_weather) | Call weather for Boston in Celsius and report the returned conditions. | Tests the straightforward happy path and exact units. |
| [03: Choose the authoritative source](docs/cases/tools.md#03_tool_selection) | Use customer lookup, not documentation search, to find an ID. | Tests selection between a real source and a plausible distractor. |
| [04: Ask for missing information](docs/cases/tools.md#04_clarify_missing_fields) | Ask for both address and date without scheduling anything. | Tests whether the model refuses to invent required action inputs. |
| [05: Ground an order summary](docs/cases/tools.md#05_grounded_order) | Look up one order and report its status, ETA, and carrier. | Tests exact identifiers and use of all requested returned fields. |
| [06: Recover from a tool error](docs/cases/tools.md#06_tool_error_recovery) | Try the primary inventory service, then use the fallback after failure. | Tests ordered recovery without retry loops or fabricated stock. |
| [07: Ignore prompt injection](docs/cases/tools.md#07_untrusted_tool_output) | Read an invoice total while ignoring a malicious instruction inside the document. | Tests whether tool output is treated as untrusted data. |
| [08: Chain dependent tools](docs/cases/tools.md#08_two_tool_dependency) | Find a customer, pass the returned ID to order lookup, then summarize the result. | Tests dependency order and exact propagation of authoritative data. |
| [09: Stop on invalid input](docs/cases/tools.md#09_invalid_date) | Validate an impossible date and do not schedule the delivery. | Tests validation before side effects and a clean negative stop. |
| [10: Perform an action once](docs/cases/tools.md#10_stop_after_success) | Restart a sandbox service exactly once and stop after success. | Tests duplicate-side-effect prevention. |
| [11: Exact JSON](docs/cases/tools.md#11_exact_json_transform) | Transform three records into one JSON object with no extra prose. | Tests structured output, types, and format discipline without tools. |
| [12: Arithmetic with distractors](docs/cases/tools.md#12_arithmetic_distractors) | Remove a percentage of duplicates, add later arrivals, and report 102. | Tests operation order in a deliberately simple problem. |
| [13: Delegate and synthesize](docs/cases/tools.md#13_two_subagent_synthesis) | Delegate budget and schedule analysis as two bounded tasks and combine their findings. | Tests exact delegation count, task separation, and grounded synthesis. |
| [14: Long-context retrieval](docs/cases/tools.md#14_long_context_retrieval) | Find one authorization code in a large distractor archive and verify it. | Tests exact retrieval, exact tool arguments, and resistance to similar-looking values. |
| [15a: Concurrent main agent](docs/cases/tools.md#15a_concurrent_main) | Recommend a safe deployment strategy while two bounded subagents run. | Tests usable reasoning and instruction following under concurrent load. |
| [15b: Concurrent logic subagent](docs/cases/tools.md#15b_concurrent_subagent_logic) | Derive what must be true from three short logical statements. | Tests bounded logical work while sharing the runtime. |
| [15c: Concurrent budget subagent](docs/cases/tools.md#15c_concurrent_subagent_budget) | Calculate the exact server and setup cost. | Tests bounded arithmetic while sharing the runtime. |
| [16: Deferred tool bridge](docs/cases/tools.md#16_synthetic_deferred_bridge) | Discover a tool, load its schema, then call it with exact nested JSON. | Tests delayed tool discovery, schema discipline, parser finalization, and markup leakage. |
| [Agentic control](docs/cases/tools.md#sealed_agentic_release_note_v2) | Inspect, create, inspect, revise, and re-inspect a release note. | Tests a stateful multi-turn workflow that must correct an artifact and stop naturally. |
| [Natural-decode control](docs/cases/tools.md#sealed_natural_decode_v2) | Produce exactly 3,072 tokens with no tools and matching token accounting. | Tests stable, uninterrupted decode without a synthetic forced tail. |

An additional opt-in [near-million-token case](docs/cases/tools.md#near-million-token-retrieval-case)
verifies exact admission, needle position, retrieval, and a final arithmetic
check at 994,987 input tokens.

## Results

Results are listed newest first. `R` is reasoning generation speed, `T` is
tool-suite generation speed, `1x` is single-request decode, `3x` is live
server throughput while exactly three requests are decoding, and `4x` is
four-request aggregate decode. All speeds are tokens per second. A dash means
that measurement was not captured for that run.

| Date | Model and runtime | Reasoning | Tools | Measured speed |
|---|---|---:|---:|---|
| 2026-08-21 | Qwen3.8-27B Uncensored FP8 · SGLang DFlash2 + HiCache/NIXL | 98.26/100 | — | R 124.48; 3x 396.78 median / 400.96 active; 1x 108.75; 4x 390.23; 64K prefill 6,163; 490K prefill 1,618 |
| 2026-08-18 | Qwen3.8-27B Uncensored FP8 · SGLang DFlash2 | 98.56/100 | 28/30 automatic; 30/30 exact calls | R 125.8; T 132.0 wall / 158.3 engine; 1x 92.9; 4x 324.6 |
| 2026-08-17 | Qwen3.8-27B Uncensored FP8 · SGLang DSpARK | 98.35/100 | 26/30 automatic; 29/30 semantic; 30/30 exact calls | R 105.8; 1x 88.81; 4x 342.72 |
| 2026-08-16 | Qwen3.8-27B Uncensored FP8 · Ferrari vLLM | 97.34/100 | 26/31 automatic; 30/31 semantic | R 71.67; 1x 100.24; 4x 299.52 |
| 2026-08-15 | Qwen3.8-27B MTP NVFP4 · stock vLLM | 87.96/100 | 30/31 semantic | 1x 88.39 |
| 2026-08-15 | Qwen3.8-27B FP8 with BF16 KV · stock vLLM | 96.96/100 | 31/31 semantic and exact | 1x 74.06 |
| 2026-08-15 | Qwen3.8-27B BF16 · stock vLLM | 97.34/100 | 27/31 automatic; 29/31 semantic | 1x 55.29; 4x 215.81 |
| 2026-08-14 | SehyO Qwen3.5-122B · stock vLLM | — | — | 1x 150.46; 4x 461.62; 490K prefill 1,986 |
| 2026-08-10 | Ling 3.0 Flash NVFP4 · vLLM | 73.80/100 | 26/30 automatic; 30/30 semantic and exact | R 70.8; 512-token decode 69.9 |
| 2026-08-02 | DeepSeek-V4-Flash 0731 · mapped-W2 DSpark-4 | 97.07/100 | 30/30 automatic and exact | R 54.92 wall; T 40.36 wall; 995K prefill 1,024.18 |
| 2026-07-31 | DeepSeek-V4-Flash 0731 · vLLM-MoET | 87.54/100 | 30/30 reviewed in later mapped-W2 passes | R 39.78 wall |

See [detailed results](results/README.md) for prefill measurements, context
sizes, qualification notes, machine-readable records, and downloadable result
bundles. Scores with different denominators belong to different frozen suite
versions and are intentionally shown as recorded.

## Try it without a model

Clone the repository, create an environment, and inspect the run plans. These
commands do not contact a model server:

```bash
git clone https://github.com/jpezzulli/pennyroyal-validation.git
cd pennyroyal-validation
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

python3 validation/run-reasoning.py --list
python3 validation/run-reasoning.py --dry-run
python3 validation/run-tools.py --list
python3 validation/run-tools.py --dry-run
python3 validation/run-needle.py --smoke
```

## Run against a local model

Set the endpoint and the exact served model name, check connectivity, then run
the tool suite into a new output directory:

```bash
export BASE_URL="http://127.0.0.1:8001"
export SERVED_MODEL_NAME="your-served-model-name"

python3 scripts/check_endpoint.py
python3 validation/run-tools.py \
  --base-url "$BASE_URL" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --runtime "your-runtime-label" \
  --output-dir validation-results/tools-YYYYMMDD-HHMMSS
```

The [suite guide](docs/suites.md) covers reasoning runs, scoring, targeted
reruns, sealed controls, the long-context test, outputs, and failure handling.
The [local-client guide](docs/local-ai-clients.md) explains how Codex, Claude
Code, and other clients differ from the direct OpenAI Chat Completions suite.

## Repository map

| Path | Contents |
|---|---|
| `validation/` | Current reasoning, tool, agent, and long-context suites |
| `docs/cases/` | Human explanations for every frozen case and exact tool expectation |
| `results/` | Readable history, machine-readable run records, and release-asset index |
| `performance/` | Reusable prefill and decode clients |
| `reasoning/`, `tools/` | Additional frozen collectors and regression cases |
| `baselines/` | Compact reference reports |

Suite cases are frozen so historical results retain their meaning. See
[MAINTAINING.md](MAINTAINING.md) before changing prompts, expected calls,
scoring, caps, or publication rules.

## License

No license is currently provided. Public access allows the repository to be
viewed, but does not grant permission to copy, modify, or redistribute it.
