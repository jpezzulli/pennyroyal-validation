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
| `validation/` | Current maintained suite imported from the `rtx-pro6000` line of `jpezzulli/vLLM-Moet` at PR #17 merge `0710574f21dc555653a87ee530f4e8ce1d87afdb` |
| `reasoning/` | Earlier standalone 64K-cap reasoning collector and frozen case material |
| `tools/` | Earlier standalone 31-invocation tool suite, including the synthetic deferred-bridge regression |
| `performance/` | Historical bounded decode and OpenAI-compatible performance clients |
| `baselines/` | Compact historical reports from the original standalone publication |
| `results/` | Curated model/run history, compact manifests, and links to detailed bundles |
| `docs/` | Case explanations, client guidance, provenance, and result policy |

The current maintained suite and the earlier standalone line are both retained
because each contains legitimate behavior not present in the other. The
current suite has strict replay/certification gates, an uncapped measured
reasoning request shape, near-million-token retrieval, and sealed agentic and
natural-decode controls. The earlier standalone line preserves the 64K
targeted-rerun contract, synthetic deferred-tool bridge, reusable performance
clients, and its compact baselines. Do not combine their scores or silently
substitute one request contract for the other.

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

## Provenance

The complete direct-API reasoning method remains archived at
`/opt/ai-artifacts/ai-testing-method` on the original machine. The maintained
public suite was first added to `jpezzulli/vLLM-Moet` by PR #3 at commit
`93810cd`, then evolved there through strict-integrity, uncapped-reasoning,
sealed-control, and concurrent-budget changes. The standalone consolidation
uses the maintained snapshot at PR #17 merge
`0710574f21dc555653a87ee530f4e8ce1d87afdb`. See
[provenance](docs/provenance.md) for the complete reconciliation record.

## License

This repository did not contain a license before public consolidation, and no
license has been added or implied by that work.
