# Reconciliation and provenance

## Source lines

The public standalone repository was reconciled from three sources:

1. `jpezzulli/pennyroyal-validation`, including the original main branch at
   `106ceea`, the standalone update line through `56e4b6f`, and draft PR #1.
2. `jpezzulli/vLLM-Moet`, default branch `rtx-pro6000`, through PR #17 merge
   `0710574f21dc555653a87ee530f4e8ce1d87afdb`.
3. `/opt/ai-artifacts/ai-testing-method`, the complete local frozen reasoning
   method and historical evidence index.

No repository history was rewritten. The maintained `validation/` subtree
was copied from the exact `vLLM-Moet` merge above and checked byte-for-byte at
consolidation. The original standalone paths remain in Git because they
contain legitimate behavior that is not a strict subset of the maintained
suite.

## Material unique to each source

| Source | Legitimate material retained |
|---|---|
| Standalone repository | 64K measured reasoning ceiling and targeted reruns; synthetic deferred-bridge regression; reusable 64K/490K prefill and natural decode clients; compact baselines; artifact index and profile overlay |
| `vLLM-Moet` maintained copy | Fail-closed replay and certification checks; corrected repeat identities; measured reasoning request with `max_tokens` omitted; near-million-token runner; exact call expectation manifest; strict unit/publication tests; sealed agentic and natural-decode controls; final 32,768-token concurrent main-agent budget |
| `/opt/ai-artifacts/ai-testing-method` | Original frozen reasoning method, protocol, rubric, clean-room handoff, compact reference reports, raw-archive locations, and historical 32K collection contract |

## `vLLM-Moet` history

The suite first entered the public runtime repository through PR #3 at commit
`93810cd` (`Publish the reproducible validation suites`). Later relevant
commits include strict certification and identity fixes, uncapped reasoning,
sealed controls, repaired control gates, and PR #17. For this consolidation,
the maintained integration snapshot is specifically:

- repository: `jpezzulli/vLLM-Moet`
- branch: `rtx-pro6000`
- PR: `#17`
- merge commit: `0710574f21dc555653a87ee530f4e8ce1d87afdb`

The distinction matters: PR #3 records the first addition; PR #17 identifies
the exact maintained source state imported into the canonical standalone home.

## Evidence authority

Repository summaries are interpreted records. Detailed local evidence remains
under `/opt/ai-artifacts` and `/opt/sglang/benchmarks/results` on the
originating system. Public release bundles preserve curated inspectable
material without deleting, reorganizing, or overwriting that archive.
