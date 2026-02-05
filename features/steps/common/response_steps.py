from __future__ import annotations

from collections.abc import Mapping

from behave import then


@then("HTTP status should be {status_code:d}")
def step_http_status(context, status_code: int) -> None:
    response = context.state.get("response")
    if response is None:
        raise AssertionError("No response available in context.state['response']")
    assert response.status_code == status_code, f"Expected {status_code}, got {response.status_code}"


@then('response should contain field "{field_name}"')
def step_response_contains_field(context, field_name: str) -> None:
    response = context.state.get("response")
    if response is None:
        raise AssertionError("No response available in context.state['response']")
    body = response.json
    if not isinstance(body, Mapping):
        raise AssertionError("Response JSON is not an object")
    assert field_name in body, f"Missing field '{field_name}' in response"
