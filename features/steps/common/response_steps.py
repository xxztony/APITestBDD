from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import re

from behave import given, then


def _get_data(context):
    return getattr(context, "http_data", None) or getattr(context, "data", None)


def _get_response(context, alias: str | None = None):
    data = _get_data(context)
    target_alias = alias or "last"
    try:
        response = data.get_response(target_alias)
    except KeyError:
        # fallback to legacy last_response
        response = getattr(context, "last_response", None)
        if response is None:
            raise
    context.last_response = response
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


def _get_field(body, path: str):
    current = body
    for part in path.split("."):
        tokens = list(re.finditer(r"([^\[\]]+)|(\[(\d+)\])", part))
        if not tokens:
            return None, False
        for token in tokens:
            key = token.group(1)
            if key is not None:
                if not isinstance(current, Mapping) or key not in current:
                    return None, False
                current = current[key]
                continue
            index = token.group(3)
            if index is not None:
                if not isinstance(current, Sequence) or isinstance(current, (str, bytes, Mapping)):
                    return None, False
                idx = int(index)
                if idx < 0 or idx >= len(current):
                    return None, False
                current = current[idx]
    return current, True


def _use_response_alias(context, alias: str) -> None:
    response = _get_response(context, alias)
    _get_data(context).put_response("last", response, overwrite=True)
    context.last_response = response


@given('I use response "{response_name}"')
def step_use_response(context, response_name: str) -> None:
    _use_response_alias(context, response_name)


@then('response "{response_alias}" status should be {status_code:d}')
def step_named_http_status(context, response_alias: str, status_code: int) -> None:
    response = _get_response(context, response_alias)
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}. Body={_body_preview(response)!r}"
    )


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
    expected = _get_data(context).resolve_placeholders(expected_value)
    assert str(value) == expected, f"Expected {field_name}={expected!r}, got {value!r}"


@then(
    'response "{left_response}" field "{left_field}" should equal '
    'response "{right_response}" field "{right_field}"'
)
def step_response_fields_equal(
    context,
    left_response: str,
    left_field: str,
    right_response: str,
    right_field: str,
) -> None:
    left = _get_response(context, left_response)
    right = _get_response(context, right_response)
    left_body = _get_json_body(left)
    right_body = _get_json_body(right)
    if not isinstance(left_body, Mapping):
        raise AssertionError(f"Response '{left_response}' JSON is not an object")
    if not isinstance(right_body, Mapping):
        raise AssertionError(f"Response '{right_response}' JSON is not an object")
    left_value, left_exists = _get_field(left_body, left_field)
    right_value, right_exists = _get_field(right_body, right_field)
    assert left_exists, f"Missing field '{left_field}' in response '{left_response}'"
    assert right_exists, f"Missing field '{right_field}' in response '{right_response}'"
    assert left_value == right_value, (
        f"Expected response '{left_response}' field '{left_field}' to equal "
        f"response '{right_response}' field '{right_field}', got {left_value!r} vs {right_value!r}"
    )


@then('I store response field "{field_name}" as "{var_name}"')
def step_store_response_field(context, field_name: str, var_name: str) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    if not isinstance(body, Mapping):
        raise AssertionError("Response JSON is not an object")
    value, exists = _get_field(body, field_name)
    assert exists, f"Missing field '{field_name}' in response"
    data = _get_data(context)
    data.put_var(var_name, value, overwrite=True)
    data.put_entity(var_name, value, overwrite=True)


@then('I save response "{response_alias}" field "{field_path}" as "{entity_alias}"')
def step_save_response_field_as_entity(context, response_alias: str, field_path: str, entity_alias: str) -> None:
    response = _get_response(context, response_alias)
    body = _get_json_body(response)
    if not isinstance(body, Mapping):
        raise AssertionError("Response JSON is not an object")
    value, exists = _get_field(body, field_path)
    assert exists, f"Missing field '{field_path}' in response '{response_alias}'"
    _get_data(context).put_entity(entity_alias, value, overwrite=True)


@then("response array size should be {size:d}")
def step_response_array_size(context, size: int) -> None:
    response = _get_response(context)
    body = _get_json_body(response)
    if not isinstance(body, Sequence) or isinstance(body, (str, bytes, Mapping)):
        raise AssertionError("Response JSON is not an array")
    assert len(body) == size, f"Expected array size {size}, got {len(body)}"

PYCODE
