# Current Pennyroyal deployment shape

This page records the portable runtime shape selected and qualified on
2026-08-27. It intentionally omits host paths, service files, credentials, and
the exact launcher. The measured evidence remains in the
[detailed qualification report](../results/qwen38-flash-next-nvfp4-final-20260827.md).

## Qualified runtime

| Field | Selected value |
|---|---|
| Hardware | One NVIDIA RTX PRO 6000 Blackwell Workstation Edition, SM120 |
| Checkpoint | `RadixArk/Qwen3.8-Flash-Next-NVFP4` |
| Qualified SGLang revision | `64ecd64924fee338e3bf846a32167cd604186827` |
| Qualified upstream baseline | `e7e78940168f3ba65c762a6f82fd8bc5b6ee04e3` |
| Installed version | `0.5.19.dev485+g64ecd6492` |
| Compute and KV | BF16 compute; FP8 E4M3 target and native-MTP KV |
| Admission | 524,288-token YaRN context; TP1; at most four running requests |
| Speculation | Native NEXTN/EAGLE; three steps; top-k 1; four draft tokens |
| Prefill | 4,096-token chunk; 16,384 maximum batched prefill tokens |
| GPU allocation | `mem_fraction_static=0.981`; 824,384 target and native-MTP KV tokens |
| Mamba state | 24 BF16 SSM slots; `extra_buffer`; tracking interval 64 |
| Accepted-state recovery | `gdn_mtp_cache_mode=none`; SM120 RecoverSSM WY output-only path |
| Linear attention | FlashInfer GDN prefill, decode, target verify, draft decode, and draft extend |
| Sparse attention | QSA with target/native-MTP shared index selection |
| MoE | FlashInfer CUTLASS target and native-MTP routed experts |
| Multimodal attention | `triton_attn`; fused Q/K RMSNorm+mRoPE correction qualified on SM120 |
| PLE | Embedding offload enabled; PLE state included in persistent hybrid state |
| Host cache | 32 GB requested HiCache memory tier; cache mode; write-through; timeout prefetch |
| Host transfer | `kernel` I/O with `page_first` layout and page size 64 |
| Persistent cache | NIXL POSIX FILE using io_uring/O_DIRECT and representation-specific namespaces |
| Reasoning defaults | Thinking enabled; launcher-owned `medium` effort |

The host allocation rounds to approximately 32.04 GB: 26.65 GB packed
target/native-MTP KV, 3.72 GB Mamba/PLE state, and 1.67 GB packed
target/native-MTP QSA index keys.

The active persistent namespace is:

```text
qwen3_8_flash_next_524k_nextn_64ecd64924_cc4649075950
```

The namespace identity is derived conservatively from checkpoint identity,
runtime revision, topology, context/cache geometry, KV and recurrent-state
dtypes, speculative configuration, and other representation-sensitive fields.
An identical configuration selects the same directory after restart; a
representation-changing configuration selects a different directory.

Mooncake is not installed or retained as a fallback. The cache-disabled
fallback is the same Flash-Next compute shape without the host-RAM and
persistent SSD tiers. The separately preserved Qwen3.8-27B/DFlash2 launcher is
a different qualified model/runtime lane, not the active deployment.

## Persistent state represented

The reusable prefix is complete only when the runtime can recover all state
required by the active model path:

- target full-attention KV;
- native-MTP KV;
- Mamba/GDN recurrent and convolution state;
- PLE accepted/request-slot state; and
- QSA compressed index keys for target and native MTP.

The 2026-08-27 qualification proved fresh write-through and same-namespace
service-restart recovery. The 489,879-token request restored 489,856 prompt
tokens and returned all three needles exactly.

## Source deltas relevant to the selected shape

The runtime carries a bounded set of source changes beyond its upstream base.
The qualification report names the exact revision rather than describing the
runtime as stock. Important active deltas include:

- day-zero Qwen3.8 Flash-Next/Qwen4 model and native-MTP integration;
- SM120 QSA sparse-decode dispatch and FP8 sparse-prefill correction;
- current-main Qwen4/MTP configuration-accessor reconciliation;
- RecoverSSM accepted-state reconstruction and the narrow SM120 FlashInfer WY
  output-only verification route for `gdn_mtp_cache_mode=none`;
- persistence of PLE state and QSA compressed index keys alongside KV and
  Mamba state;
- aligned mixed-state NIXL transfers, representation namespaces, and unique
  overlapping path-mode registration IDs; and
- the fused Qwen mRoPE correction from upstream PR #35744.

The complete frozen runtime implementation remains separately preserved. This
validation repository records the tested shape and results, not a patch series.

## Source maintenance policy

The qualified revision is an evidence boundary, not a permanent version pin.
Future source refreshes should move the upstream baseline forward and retain
only corrections that remain necessary. A refresh creates a new runtime
identity and persistent-cache namespace and must repeat focused speculative,
Mamba/PLE/QSA persistence, long-context, vision, bounded decode, reasoning, and
tool qualification before replacing this record.
