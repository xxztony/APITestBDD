from __future__ import annotations

from behave import when

from src.payloads.crds.create_user import CreateUserRequest
from src.types.crds.user_status import UserStatus


def _get_data(context):
    return getattr(context, "data", None)


def _store_response(context, response, response_name: str | None = None) -> None:
    data = _get_data(context)
    data.put_response("last", response, overwrite=True)
    if response_name:
        data.put_response(response_name, response, overwrite=False)
    context.last_response = response


def _create_crds_user_with_attributes(context, response_name: str | None = None) -> None:
    payload = CreateUserRequest.default()
    overrides = {}
    attributes = dict(payload.attributes)

    data = _get_data(context)

    for row in context.table:
        if row.headings:
            key = str(row["field"]).strip()
            value = str(row["value"]).strip()
        else:
            key = str(row[0]).strip()
            value = str(row[1]).strip()

        if not key:
            continue
        if key == "status":
            overrides["status"] = UserStatus(value)
        elif key in {"username", "email", "display_name"}:
            overrides[key] = data.resolve_placeholders(value)
        else:
            attributes[key] = data.resolve_placeholders(value)

    if attributes:
        overrides["attributes"] = attributes

    payload = payload.override(**overrides)

    system = context.systems["crds_user"]
    request_ctx = data.get_request_context()
    response = system.create_user(
        payload,
        headers=request_ctx.get("headers") or data.api_state.get("headers"),
    )
    _store_response(context, response, response_name)
    _cache_user_id(data, response)


@when("I create a CRDS user with attributes:")
def step_create_crds_user_with_attributes(context) -> None:
    _create_crds_user_with_attributes(context)


@when('I create a CRDS user with attributes as "{response_name}" response:')
def step_create_crds_user_with_attributes_as_response(context, response_name: str) -> None:
    _create_crds_user_with_attributes(context, response_name)


@when("I create a CRDS user")
def step_create_crds_user(context) -> None:
    payload = CreateUserRequest.default()
    system = context.systems["crds_user"]
    data = _get_data(context)
    request_ctx = data.get_request_context()
    response = system.create_user(payload, headers=request_ctx.get("headers") or data.api_state.get("headers"))
    _store_response(context, response)
    _cache_user_id(data, response)


@when('I create a CRDS user as "{response_name}" response')
def step_create_crds_user_as_response(context, response_name: str) -> None:
    payload = CreateUserRequest.default()
    system = context.systems["crds_user"]
    data = _get_data(context)
    request_ctx = data.get_request_context()
    response = system.create_user(payload, headers=request_ctx.get("headers") or data.api_state.get("headers"))
    _store_response(context, response, response_name)
    _cache_user_id(data, response)


@when("I query the CRDS user")
def step_query_crds_user(context) -> None:
    data = _get_data(context)
    user_id = _require_user_id(data)
    system = context.systems["crds_user"]
    request_ctx = data.get_request_context()
    response = system.query_user(user_id, headers=request_ctx.get("headers") or data.api_state.get("headers"))
    _store_response(context, response)


@when('I query the CRDS user as "{response_name}" response')
def step_query_crds_user_as(context, response_name: str) -> None:
    data = _get_data(context)
    user_id = _require_user_id(data)
    system = context.systems["crds_user"]
    request_ctx = data.get_request_context()
    response = system.query_user(user_id, headers=request_ctx.get("headers") or data.api_state.get("headers"))
    _store_response(context, response, response_name)


@when("I delete the CRDS user")
def step_delete_crds_user(context) -> None:
    data = _get_data(context)
    user_id = _require_user_id(data)
    system = context.systems["crds_user"]
    request_ctx = data.get_request_context()
    response = system.delete_user(user_id, headers=request_ctx.get("headers") or data.api_state.get("headers"))
    _store_response(context, response)


def _cache_user_id(data, response) -> None:
    body = getattr(response, "json", None)
    if isinstance(body, dict) and body.get("id"):
        user_id = str(body.get("id"))
        data.put_entity("user_id", user_id, overwrite=True)
        data.put_var("user_id", user_id, overwrite=True)


def _require_user_id(data) -> str:
    try:
        user_id = data.get_entity("user_id")
    except KeyError:
        user_id = data.get_var("user_id")
    if not user_id:
        raise AssertionError("Missing user_id in shared entities; create user first.")
    return str(user_id)

PYCODE
