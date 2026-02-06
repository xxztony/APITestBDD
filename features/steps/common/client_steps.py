from __future__ import annotations

import re

from behave import when


def _get_state(context):
    return getattr(context, "http_state", None) or context.state


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


def _resolve_placeholders(state, data):
    if not data:
        return data
    vars_map = state.get("vars") or {}
    resolved = {}
    for key, value in data.items():
        if value == "<from previous step>":
            resolved[key] = vars_map.get("last_id") or vars_map.get("user_id")
        else:
            match = re.fullmatch(r"\$\{(.+)\}", value)
            if match:
                resolved[key] = vars_map.get(match.group(1))
            else:
                resolved[key] = value
    return resolved


def _call_client(context, client_name: str, method_name: str, *, body=None, params=None):
    client = context.clients.get(client_name)
    if client is None:
        raise AssertionError(f"Client '{client_name}' not found in context.clients")
    if not hasattr(client, method_name):
        raise AssertionError(f"Client '{client_name}' has no method '{method_name}'")

    method = getattr(client, method_name)
    state = _get_state(context)
    request_ctx = state.get("request") or {}
    headers = request_ctx.get("headers") or state.get("headers")

    kwargs = {"headers": headers}
    if params:
        kwargs.update(params)
    if body is not None:
        payload_cls = getattr(context, "client_payloads", {}).get(f"{client_name}.{method_name}")
        if payload_cls:
            payload = payload_cls.default().override(**body)
            kwargs["payload"] = payload
        else:
            kwargs["payload"] = body

    response = method(**kwargs)
    state["response"] = response
    context.last_response = response
    if getattr(response, "json", None) and isinstance(response.json, dict) and response.json.get("id"):
        vars_map = state.get("vars") or {}
        vars_map["last_id"] = str(response.json.get("id"))
        vars_map.setdefault("user_id", vars_map["last_id"])
        state["vars"] = vars_map


@when('I call "{method_name}" on "{client_name}" client')
def step_call_client_no_params(context, method_name: str, client_name: str) -> None:
    _call_client(context, client_name, method_name)


@when('I call "{method_name}" on "{client_name}" client with params:')
def step_call_client_with_params(context, method_name: str, client_name: str) -> None:
    state = _get_state(context)
    params = _resolve_placeholders(state, _table_to_dict(context.table))
    _call_client(context, client_name, method_name, params=params)


@when('I call "{method_name}" on "{client_name}" client with body:')
def step_call_client_with_body(context, method_name: str, client_name: str) -> None:
    state = _get_state(context)
    body = _resolve_placeholders(state, _table_to_dict(context.table))
    _call_client(context, client_name, method_name, body=body)
