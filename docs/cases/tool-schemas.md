# Exact tool schemas

The authoritative current schemas are in
`validation/cases/tools.json` and constructed identically in
`validation/run-tools.py`. Every current function uses an object parameter
schema with `additionalProperties: false`.

## Current 30-invocation suite

| Tool | Exact properties | Required |
|---|---|---|
| `get_weather` | `location: string`; `unit: string enum[celsius,fahrenheit]` | `location`, `unit` |
| `lookup_customer` | `email: string` | `email` |
| `search_docs` | `query: string` | `query` |
| `get_order` | `order_id: string` | `order_id` |
| `list_orders` | `customer_id: string` | `customer_id` |
| `schedule_delivery` | `address: string`; `date: string` | `address`, `date` |
| `primary_inventory` | `sku: string` | `sku` |
| `fallback_inventory` | `sku: string` | `sku` |
| `fetch_document` | `document_id: string` | `document_id` |
| `validate_date` | `date: string` | `date` |
| `perform_restart` | `service: string` | `service` |
| `delegate_task` | `task: string` | `task` |
| `verify_code` | `code: string` | `code` |

Descriptions are also part of the frozen schema. In order, they identify:
current weather; exact-email customer lookup; general documentation rather
than customer records; authoritative order status; exact-customer orders;
delivery scheduling only with address and ISO date; primary inventory;
fallback inventory after primary failure; a document explicitly labeled
untrusted; Gregorian ISO date validation; one sandbox-service restart; one
bounded delegated task; and exact authorization-code verification.

## Sealed agentic control

| Tool | Exact properties | Required |
|---|---|---|
| `inspect_release_brief` | `project_id: string enum[ATLAS]` | `project_id` |
| `create_release_note` | `title: string`; `markdown: string` | `title`, `markdown` |
| `inspect_release_note` | `artifact_id: string` | `artifact_id` |
| `revise_release_note` | `artifact_id: string`; `title: string`; `markdown: string`; `review_acknowledgement: string enum[8 nodes remain unvalidated]` | all four |

These four also use `additionalProperties: false`. The exact descriptions
state that the brief is authoritative and local, creation uses Markdown,
inspection validates against the authoritative brief, and revision replaces
the note while recording the requested acknowledgement.

## Earlier synthetic deferred bridge

The legacy 31st case exposes three bridge tools. These schemas intentionally
do not declare `additionalProperties`:

- `tool_search`: object with required `query: string` and optional
  `limit: integer`.
- `tool_describe`: object with required `name: string`.
- `tool_call`: object with required `name: string` and
  `arguments: object`.

The deferred schema returned after `tool_describe` is
`synthetic_inventory_lookup` with required `sku: string` and
`include_location: boolean`; the case requires the exact nested argument
object `{"sku":"BRIDGE-731","include_location":true}`.
