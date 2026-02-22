from __future__ import annotations

from behave import given, when

from src.core.http.http_client import HttpClient


def _get_data(context):
    return getattr(context, "http_data", None) or getattr(context, "data", None)


def _get_request_context(context):
    data = _get_data(context)
    return data.get_request_context()


def _get_http_client(context):
    data = _get_data(context)
    api_state = data.api_state
    if "http_client" in api_state:
        return api_state["http_client"]
    client = getattr(context, "http_client", None)
    if client is None:
        base_url = api_state.get("base_url")
        if not base_url:
            service = api_state.get("service")
            config = getattr(context, "config_obj", None)
            if service and config:
                base_url = config.get(f"{service}.http.base_url")
                if base_url:
                    api_state["base_url"] = base_url
        if not base_url:
            raise AssertionError("Missing base_url; set it via 'I use base URL \"...\"'")
        client = HttpClient(base_url=base_url, token_manager=context.token_manager, timeout=10.0)
    api_state["http_client"] = client
    return client


def _resolve_placeholders(data, mapping):
    if not mapping:
        return mapping
    resolved = {}
    for key, value in mapping.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            inner = value[2:-1]
            try:
                resolved[key] = data.get_var(inner)
            except Exception:
                resolved[key] = data.get_entity(inner)
        else:
            try:
                resolved[key] = data.resolve_placeholders(value)
            except KeyError:
                resolved[key] = value
    return resolved


def _render_path(data, path: str) -> str:
    try:
        return data.resolve_placeholders(path)
    except KeyError as exc:
        raise AssertionError(f"Missing path variable: {exc.args[0]}") from exc


@given("I clear request context")
def step_clear_request_context(context) -> None:
    api_state = _get_data(context).api_state
    api_state["requests"] = {}
    api_state.pop("headers", None)
    api_state.pop("service", None)


@given('I use service "{service}"')
def step_use_service(context, service: str) -> None:
    _get_data(context).api_state["service"] = service


@given('I use base URL "{base_url}"')
def step_use_base_url(context, base_url: str) -> None:
    api_state = _get_data(context).api_state
    api_state["base_url"] = base_url
    api_state.pop("http_client", None)


@given('I set request header "{name}" to "{value}"')
def step_set_request_header(context, name: str, value: str) -> None:
    data = _get_data(context)
    req = _get_request_context(context)
    req["headers"][name] = data.resolve_placeholders(value)
    data.api_state["headers"] = req["headers"]


@given('I set query param "{name}" to "{value}"')
def step_set_query_param(context, name: str, value: str) -> None:
    data = _get_data(context)
    req = _get_request_context(context)
    req["params"][name] = data.resolve_placeholders(value)


@given('I set JSON field "{field}" to "{value}"')
def step_set_json_field(context, field: str, value: str) -> None:
    data = _get_data(context)
    req = _get_request_context(context)
    req["json"][field] = data.resolve_placeholders(value)


@when('I send "{method}" request to "{path}"')
def step_send_request(context, method: str, path: str) -> None:
    _send_request(context, method, path)


@when('I send "{method}" request to "{path}" with params:')
def step_send_request_with_params(context, method: str, path: str) -> None:
    params = _resolve_placeholders(_get_data(context), _table_to_dict(context.table))
    _send_request(context, method, path, params=params)


@when('I send "{method}" request to "{path}" with body:')
def step_send_request_with_body(context, method: str, path: str) -> None:
    body = _resolve_placeholders(_get_data(context), _table_to_dict(context.table))
    _send_request(context, method, path, body=body)


@when('I send "{method}" request to "{path}" as "{response_alias}" response')
def step_send_request_with_alias(context, method: str, path: str, response_alias: str) -> None:
    _send_request(context, method, path, alias=response_alias)


def _send_request(context, method: str, path: str, params=None, body=None, alias: str = "last") -> None:
    data = _get_data(context)
    api_state = data.api_state
    request_ctx = data.get_request_context()
    merged_params = dict(request_ctx.get("params") or {})
    if params:
        merged_params.update(params)
    merged_body = dict(request_ctx.get("json") or {})
    if body:
        merged_body.update(body)
    client = _get_http_client(context)
    response = client.request(
        method=method,
        path=_render_path(data, path),
        service=api_state.get("service"),
        params=merged_params or None,
        json_body=merged_body or None,
        headers=request_ctx.get("headers") or api_state.get("headers"),
    )
    data.put_response("last", response, overwrite=True)
    if alias != "last":
        data.put_response(alias, response, overwrite=False)
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
