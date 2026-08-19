# Local-AI client guide

The suite runners and coding clients do not all speak the same protocol.
`OpenAI-compatible` is therefore a family resemblance, not a complete
compatibility claim.

## Direct suite use

The runnable suites use OpenAI Chat Completions:

```bash
export BASE_URL=http://local-model-host:8001
export SERVED_MODEL_NAME=local-model
python3 scripts/check_endpoint.py
python3 validation/run-tools.py --dry-run
```

A live qualification uses `/v1/chat/completions` with streaming, tool calls,
and usage. Preserve the model's reasoning field even when a runtime calls it
`reasoning`, `reasoning_content`, or ordinary `content`.

## Codex

Current Codex custom providers use the Responses protocol. A server that
implements only `/v1/chat/completions` is not sufficient. The endpoint or a
gateway must implement the Responses request/stream/tool contract and translate
it faithfully to the local model.

User-level `~/.codex/config.toml` example:

```toml
model = "local-model"
model_provider = "local_pennyroyal"
model_context_window = 524288

[model_providers.local_pennyroyal]
name = "Local model gateway"
base_url = "http://local-model-host:8012/v1"
env_key = "LOCAL_MODEL_TOKEN"
wire_api = "responses"
requires_openai_auth = false
```

Use a placeholder only when the client or gateway requires a nonempty token:

```bash
export LOCAL_MODEL_TOKEN=local-placeholder
codex --model local-model
```

The token is client transport material, not a credential to publish. Keep
provider settings in the user-level Codex configuration; project-local
`.codex/config.toml` cannot override provider/auth keys.

Important limitations:

- The Responses API is the only supported custom-provider wire API in current
  Codex configuration.
- The local gateway must preserve tool-call identifiers, argument JSON,
  reasoning/tool event order, streaming finalization, and context accounting.
- Do not carry opaque encrypted reasoning items from an OpenAI-hosted thread
  into a local backend unless the gateway deliberately strips or translates
  them. A historical Pennyroyal experiment reached the local runtime but vLLM
  rejected inherited opaque `encrypted_content`.
- A fresh local thread is the clean compatibility test. Same-thread switching
  across unrelated providers is a separate gateway capability.
- The former OpenCodex/Pennyroyal route on the originating machine was removed;
  these instructions describe a generic future-compatible gateway, not a
  service that currently exists there.

Codex configuration keys are documented in the
[official configuration reference](https://developers.openai.com/codex/config-file/config-reference).

## Claude Code

Claude Code's custom gateway path expects the Anthropic Messages API, not
OpenAI Chat Completions. Use an adapter or gateway that exposes Anthropic
`/v1/messages` and converts messages, thinking, tools, tool results, stops,
and streaming events without changing their semantics.

```bash
export ANTHROPIC_BASE_URL=http://local-model-host:4000
export ANTHROPIC_AUTH_TOKEN=local-placeholder
export ANTHROPIC_CUSTOM_MODEL_OPTION=local-model
claude --model local-model
```

`ANTHROPIC_AUTH_TOKEN` is sent as a bearer token. `ANTHROPIC_API_KEY` is the
alternative `x-api-key` path. Use only the nonempty placeholder required by
your local gateway; never commit a live token.

With a non-first-party `ANTHROPIC_BASE_URL`, Claude Code disables MCP tool
search by default. Enable `ENABLE_TOOL_SEARCH=true` only if the gateway
actually forwards the required `tool_reference` blocks. Model discovery is a
separate opt-in gateway feature and does not make an OpenAI-only endpoint
Anthropic-compatible.

See Anthropic's official
[environment-variable](https://code.claude.com/docs/en/env-vars),
[model-configuration](https://code.claude.com/docs/en/model-config), and
[LLM-gateway](https://code.claude.com/docs/en/llm-gateway) references.

## Other compatible clients

For a generic OpenAI Chat Completions client:

1. Set the API base to `http://local-model-host:8001/v1`.
2. Set the exact served model name.
3. Supply a nonempty placeholder token only if the client refuses an empty
   value; the endpoint may ignore it.
4. Enable streaming, function tools, and enough output/context capacity.
5. Disable client-side prompt rewriting, automatic retries, or tool execution
   that would change a frozen case.
6. Verify that tool arguments arrive as JSON objects and that reasoning plus
   visible content are both retained.

## Context and reasoning

Configured context, startup KV capacity, admitted request size, and exercised
request size are different claims. Reserve room for output and client-added
instructions. A client advertising a large window does not prove the local
runtime admitted or completed it.

The suite intentionally varies reasoning behavior by contract:

- current measured reasoning omits request-level reasoning and output caps;
- current tool cases use `reasoning_effort=max`;
- the sealed agentic control uses `xhigh`;
- the sealed natural-decode control uses `low`;
- earlier standalone and historical runs used separate 32K or 64K ceilings.

Do not normalize those differences after collection.

## Troubleshooting

| Symptom | Likely boundary |
|---|---|
| `404 /v1/responses` from Codex | Endpoint is Chat-Completions-only; add a real Responses adapter |
| `404 /v1/messages` from Claude Code | Endpoint lacks Anthropic Messages compatibility |
| Model name rejected | Client alias and server's served model name differ |
| Authentication error on a no-auth local server | Client insists on a token; use a nonempty local placeholder in the documented env variable |
| Tool calls are visible text | Parser/template/gateway did not preserve structured tool events |
| Tool arguments fail JSON parsing | Model parser or gateway serialized arguments incorrectly |
| Reasoning appears missing | Runtime uses a different reasoning field or the gateway dropped it |
| Immediate length finish or no visible answer | Output budget was consumed by hidden reasoning or the endpoint applied a smaller cap |
| Long request waits with idle compute | Admission rejected the prompt-plus-output reservation; inspect the exact scheduler contract |
| False negative after correct retrieval | Check `reasoning`, `reasoning_content`, and `content` before declaring model failure |
