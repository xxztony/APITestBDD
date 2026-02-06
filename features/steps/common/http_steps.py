from __future__ import annotations

import re

from behave import given, when

from src.core.http.http_client import HttpClient


def _get_state(context):
    return getattr(context, "http_state", None) or context.state


def _get_request_context(context):
    state = _get_state(context)
    req = state.get("request")
    if req is None:
        req = {"headers": {}, "params": {}, "json": {}}
        state["request"] = req
    return req


def _get_http_client(context):
    state = _get_state(context)
    if "http_client" in state:
        return state["http_client"]
    client = getattr(context, "http_client", None)
    if client is None:
        base_url = state.get("base_url")
        if not base_url:
            raise AssertionError("Missing base_url; set it via 'I use base URL \"...\"'")
        client = HttpClient(base_url=base_url, token_manager=context.token_manager, timeout=10.0)
    state["http_client"] = client
    return client


def _resolve_placeholders(state, data):
    if not data:
        return data
    vars_map = state.get("vars") or {}
    resolved = {}
    for key, value in data.items():
        match = re.fullmatch(r"\$\{(.+)\}", value)
        if match:
            resolved[key] = vars_map.get(match.group(1))
        else:
            resolved[key] = value
    return resolved


def _render_path(state, path: str) -> str:
    vars_map = state.get("vars") or {}
    try:
        return path.format(**vars_map)
    except KeyError as exc:
        raise AssertionError(f"Missing path variable: {exc.args[0]}") from exc


@given("I clear request context")
def step_clear_request_context(context) -> None:
    state = _get_state(context)
    state["request"] = {"headers": {}, "params": {}, "json": {}}
    state.pop("headers", None)


@given('I use base URL "{base_url}"')
def step_use_base_url(context, base_url: str) -> None:
    state = _get_state(context)
    state["base_url"] = base_url
    state.pop("http_client", None)


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


@when('I send "{method}" request to "{path}"')
def step_send_request(context, method: str, path: str) -> None:
    state = _get_state(context)
    request_ctx = state.get("request") or {}
    client = _get_http_client(context)
    response = client.request(
        method=method,
        path=_render_path(state, path),
        params=request_ctx.get("params"),
        json_body=request_ctx.get("json"),
        headers=request_ctx.get("headers") or state.get("headers"),
    )
    state["response"] = response
    context.last_response = response


@when('I send "{method}" request to "{path}" with params:')
def step_send_request_with_params(context, method: str, path: str) -> None:
    state = _get_state(context)
    params = _resolve_placeholders(state, _table_to_dict(context.table))
    request_ctx = state.get("request") or {}
    merged = dict(request_ctx.get("params") or {})
    merged.update(params)
    client = _get_http_client(context)
    response = client.request(
        method=method,
        path=_render_path(state, path),
        params=merged,
        json_body=request_ctx.get("json"),
        headers=request_ctx.get("headers") or state.get("headers"),
    )
    state["response"] = response
    context.last_response = response


@when('I send "{method}" request to "{path}" with body:')
def step_send_request_with_body(context, method: str, path: str) -> None:
    state = _get_state(context)
    body = _resolve_placeholders(state, _table_to_dict(context.table))
    request_ctx = state.get("request") or {}
    merged = dict(request_ctx.get("json") or {})
    merged.update(body)
    client = _get_http_client(context)
    response = client.request(
        method=method,
        path=_render_path(state, path),
        params=request_ctx.get("params"),
        json_body=merged,
        headers=request_ctx.get("headers") or state.get("headers"),
    )
    state["response"] = response
    context.last_response = response


def _table_to_dict(table):
    if table is None:
        return {}
    data = {}
    for row in table:
        if row.headings:
            key = str(row["field"]).strip()
            value = str(row["value"]).strip()
        else:
            key = str(row[0]).strip()
            value = str(row[1]).strip()
        if key:
            data[key] = value
    return data
