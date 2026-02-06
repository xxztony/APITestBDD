# API E2E Test Framework (Behave)

A layered, enterprise‑grade framework for API E2E testing:
Feature → Step → system → client → core.

## Architecture Map

- `features/`
  - Business‑intent scenarios (Gherkin), no URL / HTTP method / token details
  - Two paths: system‑based and client‑aware
- `features/steps/`
  - Common steps (no business semantics) + business steps (call systems)
  - Client‑aware steps call “client name + method name”
- `src/systems/`
  - Business path: orchestrates client/kafka/db without leaking details
- `src/clients/`
  - API semantics: wraps HTTP endpoints only
- `src/payloads/`
  - DTOs with `default()` + `override()`
- `src/types/`
  - Enums / value types
- `src/core/`
  - `config/` configuration loading
  - `http/` HTTP + schema validation
  - `db/` database access
  - `messaging/` Kafka utilities
  - `security/` token management
  - `...` reserved: rpc / remote / observability / cache, etc.

## Done

- Core infrastructure: HTTP / Kafka / DB / token / schema / config
- API semantics: client + payload + types
- System layer: CRDS user business path
- Behave foundation: common steps + system steps + client‑aware steps
- DataTable parameterization: payload.default + override
- Tag‑driven wiring: `@api` / `@crds`

## Next

- Deep response assertions: JSONPath / array index / schema steps
- Richer client‑aware calls (nested body, type mapping)
- Fine‑grained config & credentials (multi‑env, multi‑tenant)
- Tag/router rules for multi‑system and multi‑module
- UI module isolation & wiring

## Notes

- Behave loads steps from `features/steps/` by default
- If using a custom `steps_dir`, make it relative to `features/`
