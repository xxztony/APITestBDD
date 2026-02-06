from __future__ import annotations

from collections.abc import Mapping, Sequence
import json

from behave import then


def _get_state(context):
    return getattr(context, "http_state", None) or context.state


def _get_response(context):
    state = _get_state(context)
    response = state.get("response") or getattr(context, "last_response", None)
    if response is None:
        raise AssertionError("No response available in context.state['response'] or context.last_response")
    return response


def _body_preview(response) -> str:
    text = getattr(response, "text", "")
    return text[:1000] if text else ""


def _get_json_body(response):
    body = getattr(response, "json", None)
    if body is not None:
        return body
    text = getattr(response, "text", "")
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _get_field(body: Mapping, path: str):
    current = body
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None, False
        current = current[part]
    return current, True


@then("HTTP status should be {status_code:d}")
def step_http_status(context, status_code: int) -> None:
    response = _get_response(context)
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}. Body={_body_preview(response)!r}"
    )


@then('HTTP status should be one of "{codes}"')
def step_http_status_in(context, codes: str) -> None:
    response = _get_response(context)
    expected = {int(code.strip()) for code in codes.split(",") if code.strip()}
    assert response.status_code in expected, (
        f"Expected one of {sorted(expected)}, got {response.status_code}. "
        f"Body={_body_preview(response)!r}"
    )


@then('response header "{name}" should be "{value}"')
def step_response_header_equals(context, name: str, value: str) -> None:
    response = _get_response(context)
    actual = response.headers.get(name)
    assert actual == value, f"Expected header {name}={value!r}, got {actual!r}"


@then("response should be a JSON object")
def step_response_is_object(context) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    assert isinstance(body, Mapping), "Response JSON is not an object"


@then("response should be a JSON array")
def step_response_is_array(context) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    assert isinstance(body, Sequence) and not isinstance(body, (str, bytes, Mapping)), "Response JSON is not an array"


@then('response should contain field "{field_name}"')
def step_response_contains_field(context, field_name: str) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    if not isinstance(body, Mapping):
        raise AssertionError("Response JSON is not an object")
    _, exists = _get_field(body, field_name)
    assert exists, f"Missing field '{field_name}' in response"


@then('response field "{field_name}" should be "{expected_value}"')
def step_response_field_equals(context, field_name: str, expected_value: str) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    if not isinstance(body, Mapping):
        raise AssertionError("Response JSON is not an object")
    value, exists = _get_field(body, field_name)
    assert exists, f"Missing field '{field_name}' in response"
    assert str(value) == expected_value, f"Expected {field_name}={expected_value!r}, got {value!r}"


@then('I store response field "{field_name}" as "{var_name}"')
def step_store_response_field(context, field_name: str, var_name: str) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    if not isinstance(body, Mapping):
        raise AssertionError("Response JSON is not an object")
    value, exists = _get_field(body, field_name)
    assert exists, f"Missing field '{field_name}' in response"
    state = _get_state(context)
    vars_map = state.get("vars") or {}
    vars_map[var_name] = value
    state["vars"] = vars_map


@then("response array size should be {size:d}")
def step_response_array_size(context, size: int) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    if not isinstance(body, Sequence) or isinstance(body, (str, bytes, Mapping)):
        raise AssertionError("Response JSON is not an array")
    assert len(body) == size, f"Expected array size {size}, got {len(body)}"
