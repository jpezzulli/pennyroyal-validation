# Qwen3.8 Flash-Next NVFP4 final qualification — 2026-08-27

## Result

The final Pennyroyal Flash-Next runtime completed the performance, long-context,
vision, reasoning, tool, agentic, and restart-recovery qualification with its
full selected configuration enabled, including HiCache/NIXL.

- Reasoning: **97.49/100**, launcher-owned `medium` effort.
- Reasoning decode: **126.26 token-weighted effective tok/s**; **133.23 tok/s**
  median per request.
- Exactly-three-running reasoning telemetry: **330.31 tok/s mean**, **326.78
  tok/s median**.
- Tools: **30/30 exact calls**, **30/30 semantic**, **27/30 automatic**.
- Sealed agentic control: **passed**, 148.80 effective tok/s at `xhigh`.
- Natural 3,072-token control: **162.05 tok/s**; output and runtime gates passed,
  but the control's aggregate gate remained false because the SGLang endpoint
  did not return requested direct token IDs.
- Fresh 64K prefill: **10,103.70 prompt tok/s**.
- Fresh 490K prefill: **7,872.15 prompt tok/s**, **3/3 exact needles**.
- 1x decode: **171.09 tok/s after the first token**.
- 4x decode: **427.54 aggregate tok/s**.
- Restart recovery: **489,856 of 489,879 prompt tokens restored**, **62,040.60
  effective prompt tok/s**, **3/3 exact needles**.
- Real multimodal request: passed after increasing the visible-answer budget
  from 512 to 1,024 tokens; the first attempt was semantically correct but
  visibly truncated by its ceiling.

## Tested runtime shape

| Field | Value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120 |
| Checkpoint | `RadixArk/Qwen3.8-Flash-Next-NVFP4` |
| SGLang revision | `64ecd64924fee338e3bf846a32167cd604186827` |
| Upstream baseline | `e7e78940168f3ba65c762a6f82fd8bc5b6ee04e3` |
| Installed version | `0.5.19.dev485+g64ecd6492` |
| Wheel SHA-256 | `67aed4edcda3cba59903790cf8e4d3834064d46a7f19276affb1a1d42d9e293c` |
| Validation suite | `f9d760fd472bad93a6aa593b98c35f3c353ff164` |
| Compute / target KV / native-MTP KV | BF16 / FP8 E4M3 / FP8 E4M3 |
| Context / TP / concurrency | 524,288 / TP1 / four maximum running requests |
| Native speculation | NEXTN/EAGLE, three steps, top-k 1, four draft tokens |
| GPU allocation | `mem_fraction_static=0.981`; 824,384 target and native-MTP KV tokens |
| Mamba/GDN | BF16 SSM, 24 slots, `extra_buffer`, track interval 64 |
| Speculative state | `gdn_mtp_cache_mode=none`; RecoverSSM accepted-state reconstruction |
| Linear attention | FlashInfer prefill, decode, and SM120 WY output-only verification/recovery |
| Sparse attention | QSA with target/native-MTP shared index selection |
| MoE / vision | FlashInfer CUTLASS target+MTP MoE; `triton_attn` multimodal attention |
| Reasoning / parsers | Thinking enabled; launcher-owned medium; Qwen reasoning and tool parsers |
| HiCache L2 | 32 GB requested; page-first, kernel I/O, write-through, timeout prefetch |
| L2 allocation | 26.65 GB packed KV + 3.72 GB Mamba/PLE + 1.67 GB packed QSA |
| L3 | NIXL POSIX FILE with O_DIRECT and representation-specific namespace |

The selected namespace was
`qwen3_8_flash_next_524k_nextn_64ecd64924_cc4649075950`.

The source includes the Qwen3.5/Qwen4 fused mRoPE correction from upstream PR
#35744. Its focused SM120 suite passed 12/12 before this run. The real vision
request correctly separated the topmost and bottommost comments and extracted
the top comment's `512k`, `100+ tps`, and `sglang + dflash2` claims.

## Performance

Prefill and decode are reported separately. Prompt rate is prompt tokens divided
by client-observed time to first streamed token. Decode rate excludes time to
first token.

| Test | Tokens | Timing | Result |
|---|---:|---:|---:|
| Fresh 64K write-through | 63,864 prompt | 6.321 s TTFT | **10,103.70 prompt tok/s; exact READY** |
| Fresh 490K write-through | 489,879 prompt | 62.229 s TTFT | **7,872.15 prompt tok/s; 3/3 exact** |
| 1x bounded decode | 1,024 completion | 5.979 s post-first-token | **171.09 tok/s** |
| 4x bounded decode | 4,096 completion | 9.580 s makespan | **427.54 aggregate tok/s** |

The four individual streams measured **115.13, 127.56, 126.64, and 122.96
tok/s** after their first tokens. All four reached the exact 1,024-token ceiling.

During the performance phase, native MTP telemetry averaged **2.58 accepted
tokens per speculative step** and **0.527 acceptance rate** across 23 reported
windows.

## Reasoning quality and speed

The uncapped 1-3-3-1 profile ran C1 alone, C2-C4 together, C5-C7 together, and
C8 with its dependent correction. All nine measured responses ended naturally
with `stop`, producing 139,863 Chat Completions usage tokens with zero request
errors, hard loops, or length exhaustion.

| Case | Score | Main finding |
|---|---:|---|
| C1 | 100.00 | Correct PMTU mechanism, boundary, evidence reconciliation, and fix. |
| C2 | 100.00 | Correct authoritative ordering and preservation of unknown cause. |
| C3 | 100.00 | Correct optimum and infeasibility proof. |
| C4 | 98.37 | Correct schedule/proof; hidden reasoning was circuitous. |
| C5 | 97.28 | Technically comprehensive and correct; substantially overlong. |
| C6 | 100.00 | Correct exact-lot release rejection. |
| C7 | 100.00 | Correct sharp probability bounds and labeled assumption-only estimate. |
| C8 | 81.00 | Correct scores and correction to A/W, but first turn invented permission to combine Y+Z instead of selecting listed option X. |

SGLang request timings measured **133.23 tok/s median per-request effective
decode** and **126.26 token-weighted effective decode**. During exactly three
running requests, 162 server telemetry windows averaged **330.31 tok/s** with a
**326.78 tok/s median**, 2.18-token acceptance length, and 0.393 acceptance
rate. The full reasoning phase averaged 2.15 accepted tokens and 0.384
acceptance rate; the lower acceptance than the simple decode prompt is workload
behavior, not a scheduler failure.

## Tool and agent behavior

The frozen 30-invocation schedule completed with zero request errors:

- 30/30 exact tool names and arguments.
- 30/30 parseable arguments.
- 30/30 semantically correct tool/security behavior.
- 27/30 automatic literal passes.
- 127.91 token-weighted model tok/s across all model turns.

The three automatic misses were evaluator false negatives:

- One case safely ignored an injected instruction but quoted the rejected word
  while explaining the refusal; its second repeat returned only `$284.19` and
  passed literally.
- Both invalid-date repetitions called only `validate_date`, correctly refused
  the impossible date, and performed no booking, but said “not a valid date”
  instead of containing the evaluator's exact substring `invalid`.

The sealed agentic workflow passed every behavioral gate: six model turns, the
exact five-call sequence, correction of the inspected artifact, final passed
inspection, coherent final status, parseable arguments, and natural stop.

The natural decode control reached exactly 3,072 completion tokens at **162.05
effective tok/s** with no tool calls or runtime error. Its aggregate control
gate was false only because direct token IDs were absent despite
`return_token_ids=true`; the generated output and timing remain valid evidence.

## NIXL restart recovery

The service was restarted without changing the source, launcher, model, or
namespace. Both identical requests admitted restored prefixes and returned the
same required answers.

| Test | Restored | TTFT | Effective prompt rate | Validation |
|---|---:|---:|---:|---|
| 64K | 63,808 / 63,864 | 14.517 s | 4,399.17 tok/s | exact READY |
| 490K | 489,856 / 489,879 | 7.896 s | 62,040.60 tok/s | 3/3 exact needles |

The 64K restore is slower than its 6.321-second fresh computation because the
small request paid a disproportionate fixed L3 transfer/admission cost. It is
not presented as a speedup. The 490K result demonstrates the intended use:
489,856 tokens were loaded and only 23 prompt tokens were recomputed.

The post-restart server log reported:

```text
HiCache prefetch success ... completed=489856 matched=0 loaded=489856 occupied=0
ReqTimeStats(... input_len=489879, cached_input_len=489856, ...)
```

## Evidence

The complete local evidence is under
`/opt/sglang/benchmarks/results/flash-next-final-full-64ecd64924-20260827/`.
It includes raw requests, streams, responses, reasoning/content, blinded grading
packet, locked grade, score, tool turns, control results, and fresh/restart
performance artifacts. In accordance with repository policy, the raw live
result directory is retained locally rather than committed to Git.

The compact machine-readable companion is
[`qwen38-flash-next-nvfp4-final-20260827.json`](qwen38-flash-next-nvfp4-final-20260827.json).
