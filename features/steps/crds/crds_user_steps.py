from __future__ import annotations

from behave import when

from src.payloads.crds.create_user import CreateUserRequest
from src.types.crds.user_status import UserStatus


def _get_state(context):
    return getattr(context, "http_state", None) or context.state


def _store_response(context, state, response, response_name: str | None = None) -> None:
    state["response"] = response
    context.last_response = response
    if response_name:
        responses = state.get("responses") or {}
        responses[response_name] = response
        state["responses"] = responses


def _create_crds_user_with_attributes(context, response_name: str | None = None) -> None:
    payload = CreateUserRequest.default()
    overrides = {}
    attributes = dict(payload.attributes)

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
            overrides[key] = value
        else:
            attributes[key] = value

    if attributes:
        overrides["attributes"] = attributes

    payload = payload.override(**overrides)

    system = context.systems["crds_user"]
    state = _get_state(context)
    request_ctx = state.get("request") or {}
    response = system.create_user(
        payload,
        headers=request_ctx.get("headers") or state.get("headers"),
    )
    _store_response(context, state, response, response_name)
    _cache_user_id(state, response)


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
    state = _get_state(context)
    request_ctx = state.get("request") or {}
    response = system.create_user(payload, headers=request_ctx.get("headers") or state.get("headers"))
    _store_response(context, state, response)
    _cache_user_id(state, response)


@when('I create a CRDS user as "{response_name}" response')
def step_create_crds_user_as_response(context, response_name: str) -> None:
    payload = CreateUserRequest.default()
    system = context.systems["crds_user"]
    state = _get_state(context)
    request_ctx = state.get("request") or {}
    response = system.create_user(payload, headers=request_ctx.get("headers") or state.get("headers"))
    _store_response(context, state, response, response_name)
    _cache_user_id(state, response)


@when("I query the CRDS user")
def step_query_crds_user(context) -> None:
    state = _get_state(context)
    user_id = _require_user_id(state)
    system = context.systems["crds_user"]
    request_ctx = state.get("request") or {}
    response = system.query_user(user_id, headers=request_ctx.get("headers") or state.get("headers"))
    state["response"] = response
    context.last_response = response


@when("I delete the CRDS user")
def step_delete_crds_user(context) -> None:
    state = _get_state(context)
    user_id = _require_user_id(state)
    system = context.systems["crds_user"]
    request_ctx = state.get("request") or {}
    response = system.delete_user(user_id, headers=request_ctx.get("headers") or state.get("headers"))
    state["response"] = response
    context.last_response = response


def _cache_user_id(state, response) -> None:
    body = getattr(response, "json", None)
    if isinstance(body, dict) and body.get("id"):
        vars_map = state.get("vars") or {}
        vars_map["user_id"] = str(body.get("id"))
        state["vars"] = vars_map


def _require_user_id(state) -> str:
    vars_map = state.get("vars") or {}
    user_id = vars_map.get("user_id")
    if not user_id:
        raise AssertionError("Missing user_id in http_state vars; create user first.")
    return str(user_id)
