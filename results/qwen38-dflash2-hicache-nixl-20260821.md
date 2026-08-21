# Qwen3.8-27B DFlash2 with HiCache/NIXL — 2026-08-21

## Result

The final cleaned SGLang runtime completed long-context retrieval, bounded
single and four-request decode, a three-request reasoning phase, and the full
reasoning suite without a server error, model error, hard loop, heat stop, or
length exhaustion.

- Reasoning: **98.26/100 dimension-weighted**, **98.08/100 case-weighted**.
- 64K prefill: **6,163.07 prompt tok/s**.
- 490K prefill: **1,618.31 prompt tok/s**, **3/3 exact needles**.
- 1x decode: **108.75 tok/s after first token**, **107.52 tok/s makespan**.
- 4x decode: **390.23 aggregate tok/s**.
- 3x live reasoning decode: **396.78 tok/s median**, **400.96 tok/s mean over
  the seven active-decode samples after the initial transition sample**.
- 3x DFlash acceptance: **3.98 accepted tokens**, **0.426 acceptance rate**.

## Tested runtime shape

| Field | Value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120 |
| Target | `orcarouter/Qwen3.8-27B-Uncensored-FP8` |
| Draft | `incoai/Qwen3.8-27B-DFlash2` |
| SGLang revision | `8e197ed3afc559f29562a2e7de9026f011f5d28f` |
| Upstream baseline | `5a7b26c636deb2def43640bab6c63146dbe536dc` |
| Validation revision | `56e4b6f` |
| Compute / target KV / draft KV | BF16 / FP8 E4M3 / FP8 E4M3 |
| Context / TP / concurrency | 524,288 / TP1 / four maximum running requests |
| Speculation | DFlash2, gamma 8, 2,048-token window, decode-only speculative attention |
| Prefill | 2,048-token chunked prefill and maximum prefill batch |
| GPU allocation | `mem_fraction_static=0.94`; 1,194,496 full-KV tokens |
| Mamba | 16 GPU slots; `extra_buffer_lazy`; maximum three retained states per path; FP32 SSM and BF16 convolution state |
| HiCache L2 | 96 GB requested, cache mode, write-through, timeout prefetch |
| L2 transfer | `kernel + page_first`, page size 64 |
| L3 | NIXL 1.4.0 POSIX path mode, io_uring, O_DIRECT |
| L3 cleaning | 68% high / 65% low filesystem watermarks; approximately 455–515 GB operating band on the tested filesystem |

The namespace was derived from representation-sensitive checkpoint, runtime,
topology, cache geometry, dtype, speculative, attention, Mamba, and software
identity. The selected readable suffix was `da09e1f3f870`. The exact service
launcher is intentionally not part of this result; the table records the
portable launch shape.

## Prefill and retrieval

| Test | Prompt tokens | TTFT | Prompt throughput | Result |
|---|---:|---:|---:|---|
| 64K | 63,906 | 10.369 s | **6,163.07 tok/s** | `READY` |
| Long needle | 489,921 | 302.736 s | **1,618.31 tok/s** | 3/3 exact |

The long request returned `CEDAR-7319`, `LANTERN-4826`, and `HARBOR-9054`.
Prompt throughput is prompt tokens divided by time to first token. It is not a
decode measurement. The low instantaneous rates sometimes displayed near the
end of the long prefill were per-chunk rates after attention had reached the
largest prefix, not the whole-request average.

The earlier 2026-08-17 DSpARK record showed 7,425 tok/s near 64K and 2,161
tok/s near 455K. This run is directionally about 17% and 25% lower at those two
points, but the comparison is not controlled: prompt lengths, draft method,
target KV dtype, runtime revision, cache path, and recorded power state differ.

## Bounded decode

The normal chat-completions decode requests used thinking enabled at xhigh
effort and a 1,024-token output ceiling.

| Test | Result |
|---|---:|
| 1x post-first-token decode | **108.75 tok/s** |
| 1x whole-request makespan | **107.52 tok/s** |
| 4x aggregate makespan | **390.23 tok/s** |
| 4x stream 1 | 120.79 tok/s |
| 4x stream 2 | 99.78 tok/s |
| 4x stream 3 | 102.82 tok/s |
| 4x stream 4 | 104.26 tok/s |

All four streams generated exactly 1,024 completion tokens. Relative to the
directional DSpARK record, this run was about 22% faster on the bounded single
decode and about 14% faster on the bounded four-request aggregate decode.

## Three-request reasoning speed

C5, C6, and C7 were issued simultaneously as three independent ordinary
chat-completions requests.

| Measurement | Value |
|---|---:|
| Group tokens | 70,770 |
| Group span | 434.34 s |
| Aggregate client makespan | **162.94 tok/s** |
| C5 effective rate | 109.76 tok/s |
| C6 effective rate | 133.72 tok/s |
| C7 effective rate | 137.08 tok/s |
| Exactly-3-running server median | **396.78 tok/s** |
| Exactly-3-running server mean, all 8 samples | 352.87 tok/s |
| Exactly-3-running active mean, excluding initial 16.23 transition sample | **400.96 tok/s** |
| Exactly-3-running acceptance length | **3.98** |
| Exactly-3-running acceptance rate | **0.426** |
| Two-running server mean | 239.74 tok/s |
| One-running tail server mean | 113.42 tok/s |

The group makespan number is lower than the live three-request server number
because C6 finished after 1,237 tokens and C7 after 21,882 tokens; C5 then ran
alone to 47,651 tokens. The live server values are therefore the relevant
measurement of three-request decode throughput, while group makespan is the
relevant end-to-end completion measurement for the unequal workloads.

## Reasoning quality

Qualitative scores were locked from the text-only anonymized packet before
operational token, timing, finish, loop, or server metadata was joined.

| Case | Score | Finding |
|---|---:|---|
| C1 | 98 | Correct PMTU mechanism, 1,404-byte boundary, captures, alternatives, fix, and verification. |
| C2 | 94 | Correct authoritative sequence and unknown cause; minor speculative unknowns and excess length. |
| C3 | 100 | Correct integer optimum and reduced-capacity impossibility proof. |
| C4 | 98 | Correct optimal schedule and rejection of X; longer than necessary. |
| C5 | 96 | Sound request ownership, fingerprinting, terminal results, validation, and canonical account locking. |
| C6 | 100 | Correct exact-lot release rejection. |
| C7 | 100 | Correct sharp posterior range and conditional-independence caveat. |
| C8 | 100 | Correct first decision, explicit retraction, recalculation, and replacement action. |

All nine measured responses finished with `stop`. The accepted result set
contained 169,750 locally counted tokens, zero errors, zero hard or semantic
loop events, zero heat stops, and zero output-ceiling terminations. Across all
1,120 reasoning decode samples, DFlash acceptance length averaged 3.34 and
acceptance rate averaged 0.334.

C1-C4 were collected sequentially. C5-C7 used the operator-requested concurrent
shape. C8 preserved its required first/correction turn order. A partial C5
collector attempt was excluded after a client-control mistake and did not
replace the final complete C5 response. Because the measured suite was not
all-sequential, compare the 98.26 score to earlier rows as configuration-
specific evidence rather than a controlled quality delta.

## Namespace and persistent-cache qualification

- Fresh page-64 namespace: 60,059 prompt tokens, exact needle, 12.45 seconds.
- Identical restart: 60,032 restored tokens, exact needle, 3.16 seconds.
- Page size 128 selected independent suffix `8358f46fe908`; the request was
  cold at 12.16 seconds and did not modify the page-64 namespace.
- Rollback to page size 64 selected the original `da09e1f3f870` suffix and
  restored 60,032 tokens in 4.23 seconds.
- Three-request restart restore reused approximately 180K tokens in 5.62
  seconds with all needles exact.
- A fresh low-context review found no remaining routing, determinism,
  isolation, or rollback defect after Mamba convolution dtype and checkpoint
  content identity were added to the namespace.

The final speed and reasoning campaign started only after accumulated cache
state was purged. Mooncake deployment services, packages, configuration,
staging paths, and cache roots had been removed. The runtime recreated only its
selected NIXL namespace; Mooncake was not a fallback.

## Telemetry and limitations

- Peak CPU / GPU temperature: 65 C / 52 C.
- Peak host / GPU / combined power: 563 W / 299.17 W / 851.2 W.
- Peak measured RAM / swap use: 140.75 GiB / 6.67 GiB.
- No thermal guard fired and the service completed the accepted runs without a
  restart or server error.

The tool suite was not repeated. Full-machine reboot reuse was not repeated
after namespace schema v2; process-restart reuse is directly demonstrated.
The campaign also does not isolate DFlash2 from HiCache write-through overhead,
so it does not establish the precise cause of the lower long-prefill rate.

The machine-readable companion record is
[`qwen38-dflash2-hicache-nixl-20260821.json`](qwen38-dflash2-hicache-nixl-20260821.json).
