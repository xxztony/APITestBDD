from __future__ import annotations

from behave import then


@then('resources should include {names}')
def step_resources_should_include(context, names: str) -> None:
    required = [n.strip() for n in names.split(",") if n.strip()]
    missing = [n for n in required if not context.resources.has(n)]
    assert not missing, f"Missing resources: {missing}. Available: {list(context.resources._resources.keys())}"
