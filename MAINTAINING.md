# Maintenance and publication rules

The suite is evidence infrastructure. Stability takes precedence over making
an old result look cleaner or more comparable.

## Living implementation

The repository's runners, dependencies, documentation, and validation tooling
are living code. Git commits identify exact historical states; focused unit
tests and `scripts/validate_repository.py` enforce current invariants. Do not
add a repository-wide checksum manifest that makes normal maintenance appear
to corrupt the suite. Frozen cases and published evidence remain protected by
the contracts below.

## Frozen contracts

- Frozen case identifiers remain stable.
- Do not edit a frozen prompt, correction turn, system message, output cap,
  reasoning setting, tool schema, expected call, mock result, evaluator, score
  weight, fatal condition, warm-up, order, or concurrency shape in place.
- A material suite change creates a new named version. Keep the prior version
  runnable and document why the successor exists.
- The reasoning runner's `sequential` profile remains the historical default.
  `three-user-1-3-3-1` is a separately named execution shape; changing its case
  grouping or concurrency requires another profile name rather than silently
  rewriting either schedule.
- Documentation may explain a frozen case but must not alter its behavior.
- Every published result identifies the exact repository commit and suite
  version or path.

## Runs and reruns

- Use a new output directory and immutable run identity for every attempt.
- Preserve the original attempt when a targeted rerun is authorized. A rerun
  is additional evidence, not a replacement response.
- Do not silently retry an error, loop, truncation, cap exhaustion, parser
  failure, thermal stop, or invalid schedule.
- Historical results are not silently rescored or rewritten. A later
  interpretation is a new record that cites the original evidence.
- Raw evidence and interpretation remain separate. Raw requests, responses,
  streams, telemetry, manifests, and provenance are not edited to agree with a
  report.
- A result belongs only to the tested model/runtime/configuration. Do not
  transfer it to another checkpoint, quantization, KV dtype, speculative path,
  context, power profile, client, or source revision.

## Curated history

Include a run when it is a completed qualification, a materially different
model/runtime/quantization/context/speculative path, or a failed configuration
that establishes a durable technical boundary.

Do not include every tuning attempt. Intermediate experiments enter the
curated history only when they explain a published result or a reusable failure
boundary. Mark unknown fields as unknown; never reconstruct precision from an
unrelated run.

A failed run is retained publicly only when it establishes a useful boundary.
Ordinary tuning misses, abandoned partial runs, and duplicated attempts remain
in the source archive but outside the curated index.

## Evidence packaging

- Keep summaries and machine-readable manifests in Git.
- Do not commit credentials, live environment files, model weights, caches,
  generated result directories, or machine-specific runtime debris.
- Put large immutable evidence bundles in a tagged GitHub release. Record the
  asset name, SHA-256, size, source run, and omissions in
  `results/assets.json`.
- A compact bundle may omit enormous timestamped streams or telemetry only
  when the manifest says so and preserves the original evidence location.

## Publication checklist

Before publishing a suite or result:

1. Confirm the working tree and intended branch.
2. Run the non-inference checks in the root README.
3. Verify JSON and JSON Lines structure, relative links, referenced paths, and
   exact call expectations.
4. Scan tracked and untracked candidate content for credentials, tokens,
   private keys, cookies, private data, absolute home paths, and live auth
   material.
5. Confirm every result names the exact suite commit and evidence boundary.
6. Commit only the intended files, push an intentional branch, and use the
   repository's pull-request workflow.
7. Keep the final working tree clean.
