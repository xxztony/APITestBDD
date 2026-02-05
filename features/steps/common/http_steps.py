from __future__ import annotations

from behave import given


def _get_state(context):
    return getattr(context, "http_state", None) or context.state


def _get_request_context(context):
    state = _get_state(context)
    req = state.get("request")
    if req is None:
        req = {"headers": {}, "params": {}, "json": {}}
        state["request"] = req
    return req


@given("I clear request context")
def step_clear_request_context(context) -> None:
    state = _get_state(context)
    state["request"] = {"headers": {}, "params": {}, "json": {}}
    state.pop("headers", None)


@given('I set request header "{name}" to "{value}"')
def step_set_request_header(context, name: str, value: str) -> None:
    req = _get_request_context(context)
    req["headers"][name] = value
    _get_state(context)["headers"] = req["headers"]


@given('I set query param "{name}" to "{value}"')
def step_set_query_param(context, name: str, value: str) -> None:
    req = _get_request_context(context)
    req["params"][name] = value


@given('I set JSON field "{field}" to "{value}"')
def step_set_json_field(context, field: str, value: str) -> None:
    req = _get_request_context(context)
    req["json"][field] = value
