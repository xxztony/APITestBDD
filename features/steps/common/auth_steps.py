from __future__ import annotations

from behave import given


@given("I am authenticated as CRDS user")
def step_auth_crds_user(context):
    token = context.config_obj.get("crds.auth.token")
    if not token:
        raise ValueError("Missing config: crds.auth.token (set via userdata or E2E__CRDS__AUTH__TOKEN)")
    context.token_manager.set_token("crds", token)
