# Reasoning context v2 protocol

- Suite ID: `reasoning-context-v2`.
- Cases, prompts, system message, correction turn, weights, and expected conclusions remain those in `reasoning.py`; this successor changes collection and truncation semantics, not case content.
- Endpoint: `POST /v1/chat/completions` against the explicitly recorded base URL and served model.
- Measured payloads contain the frozen messages, `stream=true`, and `stream_options.include_usage=true`. They omit `max_tokens`, temperature, top-p, top-k, seed, tools, stop sequences, and response formatting.
- A run may record an explicit request-level `reasoning_effort`; absence leaves that setting to the runtime. Results from different effort settings remain configuration-specific evidence.
- The serving runtime must default an omitted output budget to the remaining model context. A measured response ending with `finish_reason=length` invalidates the collection and must be rerun without the artificial limit. Token-budget truncation is neither a model failure nor evidence of a loop.
- Default execution is sequential C1 through C8. `--case` may select targeted cases in frozen case order; every targeted attempt uses a new output directory and remains additional evidence rather than replacing the original attempt.
- C8 correction context contains only the system message, C8 first user turn, its returned assistant response, and the frozen correction.
- Preserve requests, timestamped SSE, reconstructed reasoning/content, authoritative server usage, finish reason, timing, errors, and loop events.
- Default loop detection uses dependency-free word/punctuation equality units. Hard-loop termination requires an identical contiguous 64–1024-unit block repeated immediately four times or one normalized sentence of at least eight words repeated ten consecutive times.
- Three highly similar 256-unit reasoning windows are flagged for review but do not auto-terminate.
- Qualitative graders see response text only. Apply the `reasoning-context-v2-rubric.json` caps only after grades lock. The only mechanical caps are case-specific fatal errors and confirmed reasoning loops.
- The prior `reasoning-rubric.json` and historical collectors remain unchanged and runnable for their original results.
