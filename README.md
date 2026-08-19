# Pennyroyal validation

Pennyroyal validation is a runtime-independent library for qualifying local
models through OpenAI-compatible APIs. It preserves runnable reasoning, tool,
agent, long-context, and performance tests; the rules that keep those tests
stable; and a curated history of model/runtime configurations that established
useful capabilities or durable failure boundaries.

This is a library of tested configurations, not a leaderboard. Results belong
to the exact model, checkpoint, runtime, source revision, quantization, KV
dtype, context, speculative path, request profile, hardware, and suite commit
that produced them. Different runs are often intentionally not comparable.

## Start here

- [Suite operation](docs/suites.md) explains endpoint requirements, commands,
  outputs, scoring, reruns, and failure handling.
- [Reasoning cases](docs/cases/reasoning.md) and [tool and agent
  cases](docs/cases/tools.md) explain every frozen case.
- [Tool schemas](docs/cases/tool-schemas.md) records the exact function schema
  shapes used by the current tool suite.
- [Local-AI clients](docs/local-ai-clients.md) covers direct suite use plus the
  protocol adapters required by Codex and Claude Code.
- [Maintenance rules](MAINTAINING.md) define freezing, versioning, and result
  publication.
- [Curated runs](results/README.md) links human-readable summaries and the
  machine-readable [run index](results/runs.json).

## Repository layout

| Path | Role |
|---|---|
| `validation/` | Current maintained reasoning, tool, agent, and long-context suite |
| `reasoning/` | Earlier standalone 64K-cap reasoning collector and frozen case material |
| `tools/` | Earlier standalone 31-invocation tool suite, including the synthetic deferred-bridge regression |
| `performance/` | Historical bounded decode and OpenAI-compatible performance clients |
| `baselines/` | Compact historical reports from the original standalone publication |
| `results/` | Curated model/run history, compact manifests, and links to detailed bundles |
| `docs/` | Case explanations, client guidance, and result policy |

The current suite provides strict replay and certification gates, an uncapped
measured-reasoning request shape, near-million-token retrieval, and sealed
agentic and natural-decode controls. The repository also includes a 64K
targeted-rerun workflow, a synthetic deferred-tool bridge, reusable performance
clients, and compact reference baselines. Do not combine scores from different
request contracts or silently substitute one contract for another.

## Quick non-inference checks

These commands do not contact a model endpoint:

```bash
python3 -m unittest discover -s validation/tests -v
python3 validation/run-reasoning.py --dry-run
python3 validation/run-tools.py --dry-run
python3 validation/run-needle.py --smoke
python3 scripts/validate_repository.py
sha256sum -c SHA256SUMS
```

The checksum file covers the earlier standalone frozen assets. Mutable
orientation, generated result indexes, and repository metadata are validated
structurally instead of being frozen into that legacy manifest.

For a live run, use a fresh output directory and explicitly identify the
endpoint, served model, runtime, and exact repository commit. See
[Suite operation](docs/suites.md).


## License

This repository did not contain a license before public consolidation, and no
license has been added or implied by that work.
