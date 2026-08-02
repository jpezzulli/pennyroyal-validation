# Frozen request profiles

## Frozen comparison profile

- Launcher reasoning effort: `high`
- Launcher top-p: model default (`1.0` in the captured generation config)
- Tool harness request field: `reasoning_effort=high`
- Reasoning harness: no request-level sampling or reasoning override

## Production profile

- Launcher reasoning effort: `max`
- Launcher top-p: `0.95`
- Explicit `VLLM_USE_DEEP_GEMM=1`
- Tool harness: `tools/profiles/production-max.py`
- Reasoning harness: unchanged; it inherits launcher-level behavior

All prompts, seeds, tool schemas, deterministic tool results, grading rules,
expected outputs, output limits, warm-ups, ordering, and loop criteria remain
unchanged between these profiles.

