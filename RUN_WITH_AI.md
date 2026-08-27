# AI runner guide

This file is an instruction set for a coding agent preparing to run the
validation suite. Follow it as written. Do not start model inference during the
preparation phase.

## Your job

Prepare the repository, understand the available tests, check the local
environment safely, and tell the operator whether the validation suite is ready
to run. The operator—not you—chooses which live suite to start.

You are operating the validation scripts against a model endpoint. You do not
need to configure the tested local model as your own conversational backend.

## Safety rules

- Do not modify frozen prompts, cases, expected calls, scoring, caps, fixtures,
  or replay data.
- Do not start a live reasoning, tool, agent, performance, or long-context run
  until the operator explicitly approves one.
- Do not start, stop, restart, reconfigure, or otherwise disturb a model
  service unless the operator explicitly asks.
- Do not probe unrelated hosts, scan the network, or search for credentials.
- Do not invent endpoint details, model names, tokenizer paths, runtime labels,
  or missing measurements.
- Safe inspection, dry runs, fixture replays, unit tests, and the endpoint's
  `GET /v1/models` check are allowed during preparation.
- Preserve the first attempt of every live run. Never hide a failure with an
  automatic retry.

## 1. Obtain and identify the repository

If you do not already have a checkout:

```bash
git clone https://github.com/jpezzulli/pennyroyal-validation.git
cd pennyroyal-validation
```

Record:

```bash
git rev-parse HEAD
git status --short --branch
```

If the working tree is dirty, identify the existing changes and do not overwrite
or include them in your work.

## 2. Read the operating material

Read these files before proposing a run:

1. [`README.md`](README.md) — purpose, cases, results, and quick start.
2. [`docs/suites.md`](docs/suites.md) — exact commands, endpoint contract,
   output collection, scoring, and failure handling.
3. [`docs/cases/reasoning.md`](docs/cases/reasoning.md) — reasoning cases and
   genuine failure conditions.
4. [`docs/cases/tools.md`](docs/cases/tools.md) — tool, agent, control, and
   long-context cases.
5. [`MAINTAINING.md`](MAINTAINING.md) — frozen-case and evidence rules.

Read [`docs/local-ai-clients.md`](docs/local-ai-clients.md) only when the
operator also wants to point Codex, Claude Code, or another interactive client
directly at the local model. That protocol-adapter task is separate from
running the validation suite's Python clients.

## 3. Prepare Python and run safe checks

Use an existing suitable environment or create an isolated one:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Then run the non-inference checks:

```bash
python3 -m unittest discover -s validation/tests -v
python3 validation/run-reasoning.py --dry-run
python3 validation/run-reasoning.py \
  --execution-profile three-user-1-3-3-1 --dry-run
python3 validation/run-tools.py --dry-run
python3 validation/run-vision.py --dry-run
python3 validation/run-vision.py --smoke
python3 validation/run-needle.py --smoke
python3 scripts/validate_repository.py
```

Stop and report any failure. Do not patch the suite merely to make a check pass.

## 4. Identify the endpoint inputs

Look for values already provided by the operator or current shell environment:

- `BASE_URL`: OpenAI-compatible API base, normally without `/v1`.
- `SERVED_MODEL_NAME`: exact model ID returned by `GET /v1/models`.
- Runtime label: a precise human-readable description saved with the result.
- Tokenizer path: required for prompt construction by the current performance
  harness and for the tokenizer-exact long-context needle run.

If both endpoint variables are known, perform the safe discovery check:

```bash
python3 scripts/check_endpoint.py \
  --base-url "$BASE_URL" \
  --served-model-name "$SERVED_MODEL_NAME"
```

This check performs model discovery only; it does not submit an inference
request. If a required value is missing, report it as missing rather than
guessing.

## 5. Choose no suite yet

Prepare the exact command for the most likely requested suite, but do not run
it. The operator may choose among:

- current reasoning qualification using the historical sequential profile;
- current reasoning qualification using the named three-user 1-3-3-1 profile;
- current 30-invocation tool and agent qualification;
- one targeted ordinary tool case;
- sealed agentic control;
- sealed natural-decode control;
- current 64K/490K prefill and 1x/4x decode qualification;
- current spatial-comment vision qualification;
- opt-in near-million-token retrieval;
- a fixture replay or scoring-only task.

Every live run must use a new output directory and must record the exact
repository commit, endpoint, served model, runtime, and configuration. A
targeted rerun is additional evidence and never replaces the original attempt.

## 6. Report readiness and wait

Reply to the operator using this exact structure:

```text
Validation-suite preparation complete.

Repository
- Path: <checkout path>
- Commit: <full commit>
- Working tree: <clean, or concise description of existing changes>

Safe checks
- Unit tests: <passed or failed>
- Reasoning dry run: <passed or failed>
- Tool dry run: <passed or failed>
- Long-context smoke: <passed or failed>
- Repository validation: <passed or failed>

Endpoint
- Base URL: <value or MISSING>
- Served model: <value or MISSING>
- Model discovery: <passed, failed, or not run>
- Runtime label: <value or MISSING>
- Tokenizer path: <value, MISSING, or not needed for the proposed suite>

Readiness: <READY, READY WITH MISSING INPUTS, or BLOCKED>

Available next runs
- Reasoning qualification
- Tool and agent qualification
- Targeted tool case
- Sealed agentic control
- Sealed natural-decode control
- Near-million-token retrieval

Proposed command
<the exact command you would run after approval, or the missing information
needed to construct it>

No inference has been started. Tell me which suite to run.
```

Use `READY` only when the safe checks passed and every input for the proposed
run is known. Use `READY WITH MISSING INPUTS` when preparation succeeded but the
operator must provide endpoint or run-specific values. Use `BLOCKED` when a
safe check failed or the repository/environment cannot be prepared without a
material change.

Wait for explicit approval after sending the report.

## 7. After the operator approves a live run

- Re-read the exact command and output directory with the operator's choice.
- Run only the approved suite or case.
- Do not silently retry, rescore, or rewrite a failed result.
- Preserve raw requests, responses, streams, manifests, errors, and timings.
- Separate raw evidence from interpretation.
- Report the result, output location, failures, and any known evaluator
  limitation plainly.
