# Qwen3.8 Flash-Next DeAlign uncensored NVFP4 qualification — 2026-08-28

## Result

`dealignai/Qwen3.8-Flash-Next-UNCENSORED-NVFP4` completed the maintained
performance, long-context, reasoning, tool, vision, agentic, and
restart-recovery suites on the Pennyroyal SGLang runtime.

- Selected reasoning result: **95.55/100**, launcher-owned `medium` effort.
- Tools: **30/30 exact calls**, **30/30 semantic**, **28/30 automatic**.
- Vision: **passed** every spatial, OCR, and claim-separation check.
- Sealed agentic control: **passed**, 152.64 effective tok/s.
- Natural 3,072-token control: **149.29 effective tok/s**; generation passed,
  while the aggregate control gate remained false because the endpoint did not
  return requested direct token IDs.
- Fresh 64K prefill: **11,897.17 prompt tok/s**.
- Fresh 490K prefill: **7,842.58 prompt tok/s**, **3/3 exact needles**.
- 1x decode: **145.49 tok/s after the first token**.
- 4x decode: **408.10 aggregate tok/s** across the common post-first-token
  makespan.
- Restart recovery: **489,856 of 489,879 prompt tokens restored**, **50,404.95
  effective prompt tok/s**, **3/3 exact needles**.

## Tested runtime shape

| Field | Value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120 |
| Checkpoint | `dealignai/Qwen3.8-Flash-Next-UNCENSORED-NVFP4` |
| Checkpoint revision | `7470878ab4e42a7d439dd15cfabc654d81428cbd` |
| Weight layout | ModelOpt NVFP4 routed experts; FP8 PLE tables; BF16 excluded tensors and recurrent state |
| SGLang executable revision | `1ba0b2a1b51f7cb04d0e5a7ce4623d5c9c2cab6b` |
| Installed version | `0.5.19.dev488+g1ba0b2a1b` |
| Validation suite | `424a709ad59c992b40d7e7949bb8da8fd8c364d2` |
| Compute / target KV / native-MTP KV | BF16 / FP8 E4M3 / FP8 E4M3 |
| Context / TP / concurrency | 524,288 / TP1 / four maximum running requests |
| Native speculation | NEXTN/EAGLE, three steps, top-k 1, four draft tokens |
| GPU allocation | `mem_fraction_static=0.981`; 824,384 target/native-MTP KV tokens |
| Mamba/GDN | BF16 SSM, 24 slots, `extra_buffer`, track interval 64 |
| Attention / MoE | FlashInfer GDN; SM120 XQA through the QSA wrapper; FlashInfer CUTLASS MoE |
| HiCache | 32 GB requested; page-first, kernel I/O, write-through, timeout prefetch |
| Persistent tier | NIXL POSIX FILE with O_DIRECT |

The representation-specific namespace was
`qwen3_8_flash_next_524k_nextn_1ba0b2a1b5_7c823d3e9ca7`.

The executable source checkout carried an uncommitted 76-line
compressed-tensors NVFP4 experiment during this run. The served DeAlign
checkpoint used `--quantization modelopt_fp4`, so those compressed-tensors
changes were not the selected checkpoint path. They remain part of the exact
tracked-diff identity incorporated into the NIXL namespace and are disclosed
rather than attributed to this result.

## Performance

Prompt rate is prompt tokens divided by client-observed time to first streamed
token. Decode excludes TTFT. The 4x aggregate uses 4,096 completion tokens over
the common post-first-token makespan from the earliest first token through the
latest completion.

| Test | Tokens | Timing | Result |
|---|---:|---:|---:|
| Fresh 64K write-through | 63,864 prompt | 5.368 s TTFT | **11,897.17 prompt tok/s; exact READY** |
| Fresh 490K write-through | 489,879 prompt | 62.464 s TTFT | **7,842.58 prompt tok/s; 3/3 exact** |
| 1x bounded decode | 1,024 completion | 7.031 s post-first-token | **145.49 tok/s** |
| 4x bounded decode | 4,096 completion | 10.037 s common decode window | **408.10 aggregate tok/s** |

The four streams measured **104.36, 110.84, 101.92, and 105.62 tok/s** after
their first tokens. Their summed independent rates were 422.73 tok/s; that is
not used as the synchronized aggregate. All four reached the exact 1,024-token
ceiling.

Bounded journal samples during these tests averaged 2.33 accepted tokens and
0.443 acceptance rate at one running request. Four-running samples averaged
2.19 accepted tokens and 0.396 acceptance rate.

## Reasoning

| Case | Selected score | Main finding |
|---|---:|---|
| C1 | 100.00 | Correct PMTU mechanism, boundary, evidence, and fix. |
| C2 | 96.20 | Correct ordering; confidence caveat introduced an unsupported forward-looking possibility. |
| C3 | 100.00 | Correct optimum and reduced-capacity infeasibility proof. |
| C4 | 93.48 | Correct optimal schedule and proof; reasoning was extraordinarily long. |
| C5 | 90.22 | Sound transaction and idempotency design; reasoning was extraordinarily long. |
| C6 | 100.00 | Selected isolated rerun correctly blocks release; first concurrent attempt failed. |
| C7 | 100.00 | Correct sharp probability bounds and labeled independence estimate. |
| C8 | 82.50 | Correct correction to A/W; first turn combined Y+Z instead of selecting listed X. |

All selected responses stopped naturally with zero request errors or detected
loops. C4 generated 77,006 tokens and C5 generated 38,790. The selected C6
generated 2,068 tokens. The first concurrent C6 incorrectly authorized release;
John selected the isolated exact-contract rerun, which correctly blocked
release, as the published C6 result.

## Tools, controls, and vision

The 30-invocation tool schedule completed with zero request errors:

- 30/30 exact tool names and arguments.
- 30/30 parseable arguments.
- 30/30 semantically correct behavior.
- 28/30 automatic literal passes.

Both automatic misses were the two `05_grounded_order` repetitions. Each made
the exact required `get_order` call and returned the correct status, ETA, and
carrier, but rendered ISO date `2026-08-03` as `August 3, 2026`.

The sealed agentic control passed all behavioral gates: six model turns, the
exact five-call workflow, a real corrected artifact, passed final inspection,
and natural stop. It measured 152.64 effective tok/s.

The natural decode control reached exactly 3,072 tokens at 149.29 effective
tok/s with no tool calls or runtime errors. Its aggregate gate was false only
because direct token IDs were absent.

The ordinary multimodal Chat Completions case passed all checks. It correctly
separated the topmost and bottommost comments and extracted `512k`, `100+ tps`,
and `sglang + dflash2` from the top comment.

## NIXL restart recovery

Before restart, the selected namespace occupied approximately 20 GB across
35,294 files. The service restarted without changing the launcher, checkpoint,
source identity, or namespace. The identical 490K request then reported:

```text
HiCache prefetch success ... completed=489856 matched=0 loaded=489856 occupied=0
ReqTimeStats(... input_len=489879, cached_input_len=489856, ...)
```

| Prompt | Restored | Recomputed | TTFT | Effective prompt rate | Validation |
|---:|---:|---:|---:|---:|---|
| 489,879 | 489,856 | 23 logical tokens | 9.719 s | **50,404.95 tok/s** | **3/3 exact needles** |

The request completed normally after restoring the hybrid prefix. Final service
health showed the same model identity, 524,288-token admission, zero automatic
restarts, and no CUDA errors, OOMs, retractions, tracebacks, or exceptions.

## Evidence boundary

Complete local evidence is retained under
`/opt/sglang/upstream-prep/validation-results/dealignai-qwen38-flash-next-nvfp4-20260828-1853/`.
It includes requests, raw SSE, reconstructed responses, the selected grade,
tool turns, vision artifacts, controls, performance results, and restart
evidence.

Raw live artifacts and hidden reasoning remain local rather than being
committed. The compact machine-readable companion is
[`qwen38-flash-next-dealignai-uncensored-nvfp4-20260828.json`](qwen38-flash-next-dealignai-uncensored-nvfp4-20260828.json).
