from __future__ import annotations

from behave import given


@given('I set request header "{name}" to "{value}"')
def step_set_request_header(context, name: str, value: str) -> None:
    headers = context.state.get("headers") or {}
    headers[name] = value
    context.state["headers"] = headers
