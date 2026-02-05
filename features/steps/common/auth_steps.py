from __future__ import annotations

from behave import given


@given('I am authenticated as "{service}"')
def step_auth_service(context, service: str) -> None:
    key = f"{service}.auth.token"
    token = context.config_obj.get(key)
    if not token:
        raise ValueError(f"Missing config: {key} (set via userdata or E2E__{service.upper()}__AUTH__TOKEN)")
    context.token_manager.set_token(service, token)
