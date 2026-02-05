from __future__ import annotations

from behave import when

from src.payloads.crds.create_user import CreateUserRequest
from src.types.crds.user_status import UserStatus


@when("I create a CRDS user with attributes:")
def step_create_crds_user_with_attributes(context) -> None:
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
    response = system.create_user(
        payload,
        headers=context.state.get("headers"),
    )
    context.state["response"] = response
