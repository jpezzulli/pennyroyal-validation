# Suite operation

## What the suites evaluate

| Suite | Capability |
|---|---|
| Current reasoning | Closed-book diagnosis, evidence ordering, constrained optimization, scheduling proof, idempotent transaction design, rule-based release, probability bounds, and multi-turn correction |
| Current tools and agents | Direct answers, exact tool choice and arguments, clarification, dependency ordering, recovery, untrusted output, invalid input, one-shot control, JSON, arithmetic, delegated synthesis, long-context retrieval, and concurrent main/subagent work |
| Sealed controls | A stateful inspect-create-inspect-revise-inspect artifact workflow and a fixed natural-decode instrument |
| Near-million-token needle | Tokenizer-exact admission, retrieval, response-field extraction, prefill/decode timing, and immediate post-run health |
| Earlier standalone line | The 64K reasoning/targeted-rerun contract, synthetic deferred-tool bridge, and reusable performance clients |

The current maintained suite lives in `validation/`. The earlier standalone
line remains runnable in `reasoning/`, `tools/`, and `performance/`.
They are distinct frozen contracts. A score from one is not silently converted
to the other.

## Endpoint contract

The live collectors require:

- `GET /v1/models` with the requested served model visible;
- `POST /v1/chat/completions`;
- streaming Server-Sent Events with a terminal `[DONE]`;
- ordinary OpenAI chat messages and function-tool definitions;
- assistant tool calls with JSON-decodable arguments;
- usage fields when `stream_options.include_usage=true`;
- enough admitted context for prompt plus reserved output;
- no hidden endpoint-side mutation of prompts, tools, caps, seeds, or
  reasoning settings.

`/metrics`, system-journal access, token-ID return, and
`/v1/chat/completions/render` are optional except for the specific controls
that say they require them. The near-million-token runner requires the render
endpoint because it verifies the server's exact rendered token count before
submitting the expensive request.

Defaults are `BASE_URL=http://127.0.0.1:8001` and
`SERVED_MODEL_NAME=pennyroyal`. Override both explicitly for another host:

```bash
export BASE_URL=http://local-model-host:8001
export SERVED_MODEL_NAME=local-model
python3 scripts/check_endpoint.py
```

The suite runners do not require or invent an API credential. If an
OpenAI-compatible gateway insists on a nonempty bearer token, configure that
gateway or client outside the frozen case definitions.

## Current reasoning suite

Inspect without inference:

```bash
python3 validation/run-reasoning.py --list
python3 validation/run-reasoning.py --dry-run
python3 validation/run-reasoning.py \
  --replay validation/fixtures/reasoning-replay.jsonl
python3 validation/score-reasoning.py \
  --grade validation/fixtures/reasoning-dspark4-grade.json
```

Collect a new run:

```bash
python3 validation/run-reasoning.py \
  --base-url "$BASE_URL" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --runtime exact-model-runtime-label \
  --tokenizer-path /path/to/model-or-tokenizer \
  --output-dir validation-results/reasoning-YYYYMMDD-HHMMSS
```

The two warm-ups are not scored. The nine measured requests omit
`max_tokens`, request-level sampling, and reasoning overrides. The endpoint
or launcher therefore owns the measured output ceiling and reasoning defaults.
Record those values in result provenance.

Create the metadata-free packet before grading, lock qualitative grades, then
apply mechanical caps:

```bash
python3 validation/anonymize-reasoning.py \
  --suite validation/cases/reasoning.py \
  --results validation-results/reasoning-YYYYMMDD-HHMMSS/results.jsonl \
  --output validation-results/reasoning-YYYYMMDD-HHMMSS/grading-packet.json
```

The current collector does not implement a single-case live rerun. The earlier
standalone collector supports `--case CASE_ID`; use a fresh output directory
and retain the original attempt. Do not claim that a targeted legacy rerun was
part of the current uncapped suite.

## Current tool and agent suite

Inspect or replay without live model calls:

```bash
python3 validation/run-tools.py --list
python3 validation/run-tools.py --dry-run
python3 validation/run-tools.py \
  --replay validation/fixtures/tools-dspark4-replay.json
```

Run all 30 invocations:

```bash
python3 validation/run-tools.py \
  --base-url "$BASE_URL" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --runtime exact-model-runtime-label \
  --output-dir validation-results/tools-YYYYMMDD-HHMMSS
```

Run one ordinary case as a correction or diagnostic:

```bash
python3 validation/run-tools.py \
  --only-case 06_tool_error_recovery \
  --base-url "$BASE_URL" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --runtime exact-model-runtime-label \
  --output-dir validation-results/tool-rerun-YYYYMMDD-HHMMSS
```

The targeted run is additional evidence and is not a 30-invocation
qualification. Tool execution is local and deterministic; no external weather,
customer, order, inventory, delivery, document, restart, delegation, or
verification service is contacted.

## Sealed controls

Inspect definitions:

```bash
python3 validation/run-tools.py --control agentic --dry-run
python3 validation/run-tools.py --control natural-decode --dry-run
```

Each live control requires a unique 16-to-80-character cache partition:

```bash
python3 validation/run-tools.py \
  --control agentic \
  --cache-key AGENTIC-RUN-0000000000000001 \
  --runtime exact-model-runtime-label \
  --output-dir validation-results/agentic-YYYYMMDD-HHMMSS

python3 validation/run-tools.py \
  --control natural-decode \
  --cache-key NATURAL-RUN-0000000000000001 \
  --runtime exact-model-runtime-label \
  --output-dir validation-results/natural-decode-YYYYMMDD-HHMMSS
```

The agentic control uses `reasoning_effort=xhigh` and a 32,768-token ceiling.
The natural-decode control uses `reasoning_effort=low`, temperature zero, no
tools, and a 3,072-token ceiling.

## Near-million-token needle

Safe checks:

```bash
python3 validation/run-needle.py --list
python3 validation/run-needle.py --dry-run
python3 validation/run-needle.py --smoke
```

The full run is opt-in:

```bash
python3 validation/run-needle.py \
  --base-url "$BASE_URL" \
  --served-model-name "$SERVED_MODEL_NAME" \
  --tokenizer /path/to/model-or-tokenizer \
  --target-input-tokens 994987 \
  --output-dir validation-results/needle-YYYYMMDD-HHMMSS \
  --i-understand-this-may-take-20-minutes
```

Do not run this merely to fill a missing historical field. It is an exceptional
capacity/retrieval qualification.

## Outputs and scoring

Reasoning collection preserves request JSON, timestamped SSE, reconstructed
reasoning/content, usage, finish state, timings, errors, loop events, a run
manifest, and the blinded grading packet. Reasoning scores use the frozen
0-to-4 rubric dimensions and case weights; reviewer judgment is required.

Tool collection preserves every model turn, tool call/result, final text,
invocation identity, errors, and a manifest. Report at least schedule integrity,
automatic behavioral passes, exact tool selection and arguments, parseable
arguments, errors and finish states, and semantic review where a literal
matcher may be a false negative.

Automatic and semantic scores answer different questions. A literal date or
wording mismatch may fail the automatic gate while tool selection and arguments
remain exact. Conversely, exact calls do not rescue fabricated final text,
ignored tool results, repeated side effects, or a missing visible answer.

## Failure handling

- Preserve the first failed attempt and its raw evidence.
- Do not edit the case or evaluator to make a candidate pass.
- Distinguish endpoint errors, parser errors, schedule-integrity failures,
  cap/truncation, evaluator false negatives, and genuine model failures.
- Record the exact runtime/configuration boundary. Do not transfer a failure to
  a different checkpoint or runtime.
- Retain a failed run in the curated public history only when it establishes a
  durable and useful technical boundary.

## Raw evidence versus interpretation

Raw evidence is what the client and server emitted: requests, responses,
streams, manifests, token IDs, telemetry, and source/config provenance.
Interpretation is the grade, semantic review, comparison, selection decision,
or explanation. Reports cite raw evidence; they never replace or rewrite it.
