# Current Pennyroyal deployment shape

This page records the portable runtime shape selected after the 2026-08-21
qualification. It intentionally omits host paths, service files, credentials,
and the exact launcher. The measured evidence remains in the
[detailed qualification report](../results/qwen38-dflash2-hicache-nixl-20260821.md).

## Qualified runtime

| Field | Selected value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120 |
| Target | `orcarouter/Qwen3.8-27B-Uncensored-FP8` |
| Draft | `incoai/Qwen3.8-27B-DFlash2` |
| Qualified SGLang revision | `8e197ed3afc559f29562a2e7de9026f011f5d28f` |
| Qualified upstream baseline | `5a7b26c636deb2def43640bab6c63146dbe536dc` |
| Compute and KV | BF16 compute; FP8 E4M3 target and draft KV |
| Admission | 524,288-token context; TP1; at most four running requests |
| Speculation | DFlash2; gamma 8; 2,048-token window; decode-only speculative attention |
| Prefill | 2,048-token chunk and maximum prefill batch |
| GPU allocation | `mem_fraction_static=0.94`; 1,194,496 full-KV tokens |
| Mamba state | 16 GPU slots; `extra_buffer_lazy`; maximum three retained states per path; FP32 SSM and BF16 convolution state |
| Host cache | 96 GB requested HiCache memory tier; cache mode; write-through; timeout prefetch |
| Host transfer | `kernel` I/O with `page_first` layout and page size 64 |
| Persistent cache | NIXL 1.4.0 POSIX FILE path using io_uring and O_DIRECT |
| Persistent cleaning | 68% high and 65% low filesystem watermarks; approximately 455–515 GB measured operating band |
| Reasoning defaults | Thinking enabled; high, xhigh, or max effort according to the client profile |

The persistent namespace is derived conservatively from the target and draft
checkpoint identity, runtime revision, topology, context and cache geometry,
KV and Mamba dtypes, speculative configuration, and other representation-sensitive
settings. An identical configuration selects the same directory after restart;
a representation-changing configuration selects a different directory. The
qualified page-size-64 namespace used suffix `da09e1f3f870`.

Mooncake is not installed as a fallback. The operational fallback is the same
target and DFlash2 shape with the host-RAM and persistent SSD cache tiers
disabled.

## Source maintenance policy

The qualified revision above is an evidence boundary, not a permanent fork or
version pin. The deployment tracks current upstream SGLang `main` and should be
refreshed by moving the source baseline forward, then retaining only the
smallest corrections that remain necessary. Obsolete, transient-workload, and
deployment-specific source changes are removed during that reconciliation.

As of 2026-08-22, upstream `main` was
`eec794bce0808ae26cc1dcb84a56b65d2df82af5`, 93 upstream commits ahead of the
qualified local branch. That newer source had not yet replaced the qualified
runtime, so results in this repository must continue to name the tested
revision until a new qualification is completed.

The next refresh should begin from current `main`, not by extending the old
baseline with an indefinite cherry-pick series. Corrections not yet upstream
remain temporary deltas and should disappear as their upstream equivalents
land.

## Relevant upstream work reviewed on 2026-08-22

| Upstream work | Applicability to this deployment | Disposition |
|---|---|---|
| [SGLang #35455](https://github.com/sgl-project/sglang/pull/35455) | Calibrated compressed-tensors KV scales. The selected checkpoints do not declare that KV scheme and produced no dropped-scale warnings. | Already merged; no behavioral change for this deployment. |
| [SGLang #35496](https://github.com/sgl-project/sglang/pull/35496) | Quantized target `lm_head` support for DFlash2. The selected target has a dense BF16 `lm_head` explicitly excluded from FP8 weight conversion. | Already merged; useful for future quantized-head targets, not a current speed path. |
| [SGLang #35579](https://github.com/sgl-project/sglang/pull/35579) | CUDA-graph follow-up for the quantized-head selector. | Closed draft; not applicable to the selected BF16 head. |
| [SGLang #35663](https://github.com/sgl-project/sglang/pull/35663) | DFlash2 documentation and cookbook material. | Already merged; documentation only. |
| [SGLang #35744](https://github.com/sgl-project/sglang/pull/35744) | Correct mRoPE routing in the fused Qwen Q/K RMSNorm and RoPE kernel. | Relevant when native vision is enabled; qualify one real image path after inclusion. |
| [SGLang #35798](https://github.com/sgl-project/sglang/pull/35798) | Exact CDF-boundary correction in target-only speculative sampling. | Small correctness fix directly relevant to non-greedy DFlash2 sampling. |
| [SGLang #35821](https://github.com/sgl-project/sglang/pull/35821) | Prevents zero-length Mamba radix ghost nodes and clamps speculative state tracking. | Directly relevant, but the DFlash2 worker has a separate tracking implementation that must be reconciled and tested rather than assumed covered. |
| [SGLang #35936](https://github.com/sgl-project/sglang/pull/35936) | Attempts to stop server-side generation after client disconnect. | The failure is locally relevant, but the reviewed revision's prefix matching could abort unrelated request IDs; do not apply it unchanged. |
| [SGLang #36014](https://github.com/sgl-project/sglang/pull/36014) | Aligns Triton GDN beta precision between packed decode and target verification. | Strongest directly applicable speculative-correctness correction for this runtime. |

These items are correctness, state-lifecycle, sampling, cancellation, or vision
changes. They do not establish a decode-speed improvement for the selected
block-FP8 target with a BF16 language-model head.

## Qualification boundary after an update

A source refresh creates a new runtime identity and a new persistent-cache
namespace. Before replacing the qualified runtime, the refreshed build should
repeat focused speculative/Mamba tests, a thinking-enabled smoke pass, long
prefill and needle retrieval, bounded 1x and concurrent decode, and the
reasoning/tool profiles selected for publication. Historical numbers remain
attached to the exact revision that produced them.
