# Frozen reasoning cases

The authoritative prompts, answer keys, and fatal conditions are in
`validation/cases/reasoning.py`. This document explains them; it does not
replace or modify them.

## Shared request and scoring contract

All cases are closed-book and expose no tools. C1 through C7 are single-turn.
C8 adds one fixed correction turn, so the suite produces nine measured
requests. The current collector omits `max_tokens`, sampling, and
request-level reasoning overrides. The earlier standalone collector uses a
65,536-token measured ceiling, while historical reference runs used 32,768.
Those are separate contracts.

Each applicable dimension is scored 0 to 4:

| Dimension | Weight |
|---|---:|
| Correctness | 24 |
| Evidence discipline | 10 |
| Contradiction detection | 10 |
| Constraint preservation | 10 |
| Technical reasoning | 14 |
| Unsupported assumptions | 8 |
| Confidence calibration | 6 |
| Revision quality | 8 |
| Loop behavior | 6 |
| Final-answer usability | 4 |

Case weights apply within dimensions; C8 alone supplies revision quality.
Qualitative grades are locked from metadata-free text before finish state,
tokens, timing, runtime identity, or loop flags are revealed. Mechanical caps
are 35 for a case-specific fatal error, 20 for a confirmed reasoning loop, and
10 for repetitive 32,768-token exhaustion without a usable answer.

## Case library

### C1: Tunnel latency diagnosis

- Weight: 14.
- Capability: network diagnosis under a precise MTU boundary and conflicting
  but reconcilable capture points.
- Why it exists: polished models often blame a visible warning or application
  symptom instead of calculating the packet-size threshold.
- Request shape: identify the mechanism, explain both captures and the
  1,404-byte boundary, reject distractions, and give the smallest correction
  plus verification.
- Expected behavior: conclude PMTU black hole; calculate
  `1500 - 96 = 1404`; explain pre- versus post-encapsulation capture; connect
  the retransmission timeout to the delay; clamp inner MTU/MSS to at most 1404
  or allow valid PTB; reject fan, DNS, CPU, GC, and application alternatives.
- Genuine failure: selects an unsupported primary cause or only increases a
  timeout.
- Evaluator boundary: minor extra protocol detail is a deduction only when it
  is unsupported; it is not automatically fatal if the required mechanism and
  correction remain sound.

### C2: Authoritative ordering versus client logs

- Weight: 12.
- Capability: evidence authority and event ordering with clock skew,
  optimistic UI state, queueing, and receipt-order distractions.
- Why it exists: models frequently prefer earlier wall-clock or witness
  evidence over a signed application sequence.
- Request shape: decide whether the X-to-Y write caused the first alarm,
  reconcile every conflict, and state what remains unknown.
- Expected behavior: sequence 441 has X, 442 activates the alarm, and 443
  applies Y; the write therefore cannot cause the first alarm through the
  stated mechanism. Workstation and SIEM evidence show intent/reporting, not
  controller application. The actual cause remains unknown.
- Genuine failure: attributes the first alarm to the write or invents another
  cause.
- Evaluator boundary: the answer may discuss plausible categories only if they
  are clearly unknown and not asserted as the cause.

### C3: Production optimization with grade mix

- Weight: 14.
- Capability: whole-batch constrained integer optimization with quantity,
  grade mix, energy, capacity, and sunk-cost distractions.
- Why it exists: common failures use fractional batches, discard output to
  manipulate grade share, or stop at the first quantity-feasible plan.
- Request shape: find the minimum-cost feasible plan, prove every constraint,
  and re-evaluate feasibility when A capacity falls to five.
- Expected behavior: reject 5A+6B because 468/1020 is 45.9% Grade H; select
  6A+5B with 1,026 accepted, 522 H (50.9%), 405 energy, and $4,048 cost; show
  7A+4B is feasible but costs $4,136; prove no plan survives A max five; ignore
  the sunk audit fee.
- Genuine failure: fractional batches, discarded units, violated constraints,
  nonoptimal selection, or claimed reduced-capacity feasibility.
- Evaluator boundary: an alternative proof is valid if it establishes the same
  integer optimum and infeasibility.

### C4: Constrained non-preemptive schedule

- Weight: 14.
- Capability: release times, two constrained resources, precedence,
  non-preemption, maintenance, deadlines, and lexicographic objectives.
- Why it exists: presenting one feasible Gantt chart is easier than proving the
  minimum makespan and correctly rejecting an optional job.
- Request shape: schedule all mandatory jobs, decide optional X, and prove the
  earliest F completion.
- Expected behavior: B 0-2, E 2-4, H 4-6, C 4-8, maintenance 6-8, A 8-11,
  D 11-15, F 15-17; prove 17 is minimal because B+E+H consume all six
  pre-maintenance GPU hours and A+D consume seven post-maintenance hours;
  reject X because it pushes H and F later.
- Genuine failure: accepts X, overlaps specialist work, straddles maintenance,
  violates a deadline, or claims a makespan below 17.
- Evaluator boundary: equivalent resource-feasible schedules are acceptable
  only if they preserve the same optimal makespan and exclusion proof.

### C5: Idempotent transfer implementation review

- Weight: 16.
- Capability: concurrent transaction design, idempotency ownership, request
  fingerprints, terminal outcomes, validation, missing rows, lock ordering,
  and deadlock behavior.
- Why it exists: this is the suite's strongest discriminator. Models often
  assume a transaction plus unique key is sufficient while leaving duplicate
  outcomes inconsistent or money/account invariants unsafe.
- Request shape: identify all correctness failures and give the smallest sound
  transaction/locking order.
- Expected behavior: reject the outside-transaction idempotency check; explain
  duplicate races; atomically claim request ID plus fingerprint; reject changed
  parameters; validate positive integer cents, distinct existing accounts, and
  both rows; lock both accounts in canonical ID order; persist every terminal
  outcome including insufficient funds; handle remaining deadlock aborts.
- Genuine failure: declares the code safe or proposes a patch that permits
  inconsistent duplicates, request-ID substitution, or money loss.
- Evaluator boundary: different SQL primitives are acceptable if they preserve
  the same ownership, fingerprint, locking, and durable-outcome invariants.
  Excessive length can hide an otherwise correct design but is graded
  separately from correctness.

### C6: Release decision with distractions

- Weight: 10.
- Capability: exact identity, evidence carry-forward rules, waiver scope, and
  refusal under urgency and authority pressure.
- Why it exists: models often treat a truncated display, manager note, or
  supplier history as permission to bypass an explicit release rule.
- Request shape: decide whether shipping lot L17-R may be released and identify
  controlling evidence.
- Expected behavior: block release because L17-R lacks T1; old L17 results do
  not transfer; the waiver cannot replace T1 and T2 is available; truncated UI,
  history, urgency, and generic note do not satisfy the rule.
- Genuine failure: authorizes release.
- Evaluator boundary: operational suggestions may follow, but the release
  decision must remain unambiguous.

### C7: Posterior probability without independence

- Weight: 10.
- Capability: partial-identification bounds and disciplined separation of an
  optional independence assumption.
- Why it exists: models routinely multiply marginal conditional rates and
  present a single posterior as determined.
- Request shape: state what can and cannot be calculated, give the sharp range,
  and optionally label an independence-only estimate.
- Expected behavior: exact posterior is unidentified; joint-positive
  probability is [0.50, 0.70] under disease and [0, 0.10] without disease;
  sharp posterior range is about 35.7% to 100%; independence gives about 75.7%
  only as an unsupported assumption.
- Genuine failure: presents 75.7% or any single posterior as determined.
- Evaluator boundary: equivalent exact fractions or more precise decimals are
  acceptable.

### C8: Fixed multi-turn correction

- Weight: 10.
- Capability: arithmetic decision rules, ambiguity sets, safe containment, and
  explicit belief revision after corrected evidence.
- Why it exists: models may patch the old conclusion instead of recalculating,
  silently alter unaffected facts, or fail to retract the earlier action.
- Request shape: first score A/B/C and choose containment; then apply one fixed
  correction and state the retraction, retained facts, and new action.
- Expected behavior: first A=3, B=4, C=5, ambiguous B/C, choose X; after the
  correction A=7, B=4, C=-2, unique A, choose W; retract B/C ambiguity and X
  while retaining initial scores, E1, E2, rule, and action table.
- Genuine failure: retains B/C or X, ignores the correction, or changes
  unaffected evidence.
- Evaluator boundary: both turns are one case. Revision quality is not scored
  from any other case.

## Known evaluator limitations

The rubric is deliberately human-reviewed. It does not promise that another
grader will reproduce an old decimal exactly. Literal operational facts,
finish state, loop detection, and fatal caps are applied only after qualitative
scores are locked. A long but correct answer may lose loop-efficiency or
usability points without becoming a technical failure; a concise unsafe answer
does not escape a fatal cap.
