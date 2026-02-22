from __future__ import annotations

from behave import when


def _get_data(context):
    return getattr(context, "http_data", None) or getattr(context, "data", None)


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


def _resolve_placeholders(data, mapping):
    if not mapping:
        return mapping
    resolved = {}
    for key, value in mapping.items():
        if value == "<from previous step>":
            try:
                resolved[key] = data.get_entity("last_id")
            except Exception:
                resolved[key] = data.get_var("last_id")
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            inner = value[2:-1]
            try:
                resolved[key] = data.get_var(inner)
            except Exception:
                resolved[key] = data.get_entity(inner)
        else:
            resolved[key] = data.resolve_placeholders(value)
    return resolved


def _call_client(context, client_name: str, method_name: str, *, body=None, params=None):
    client = context.clients.get(client_name)
    if client is None:
        raise AssertionError(f"Client '{client_name}' not found in context.clients")
    if not hasattr(client, method_name):
        raise AssertionError(f"Client '{client_name}' has no method '{method_name}'")

    method = getattr(client, method_name)
    data = _get_data(context)
    request_ctx = data.get_request_context()
    headers = request_ctx.get("headers") or data.api_state.get("headers")

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
    data.put_response("last", response, overwrite=True)
    context.last_response = response
    if getattr(response, "json", None) and isinstance(response.json, dict) and response.json.get("id"):
        last_id = str(response.json.get("id"))
        data.put_entity("last_id", last_id, overwrite=True)
        data.put_entity("user_id", last_id, overwrite=True)
        data.put_var("last_id", last_id, overwrite=True)
        data.put_var("user_id", last_id, overwrite=True)


@when('I call "{method_name}" on "{client_name}" client')
def step_call_client_no_params(context, method_name: str, client_name: str) -> None:
    _call_client(context, client_name, method_name)


@when('I call "{method_name}" on "{client_name}" client with params:')
def step_call_client_with_params(context, method_name: str, client_name: str) -> None:
    data = _get_data(context)
    params = _resolve_placeholders(data, _table_to_dict(context.table))
    _call_client(context, client_name, method_name, params=params)


@when('I call "{method_name}" on "{client_name}" client with body:')
def step_call_client_with_body(context, method_name: str, client_name: str) -> None:
    data = _get_data(context)
    body = _resolve_placeholders(data, _table_to_dict(context.table))
    _call_client(context, client_name, method_name, body=body)


@when('I call "{method_name}" on "{client_name}" client as "{response_alias}" response')
def step_call_client_with_alias(context, method_name: str, client_name: str, response_alias: str) -> None:
    _call_client(context, client_name, method_name)
    context.data.put_response(response_alias, context.last_response, overwrite=False)

PYCODE
