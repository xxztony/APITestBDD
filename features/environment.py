from __future__ import annotations

import logging
import os
import sys
from typing import Any

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config.config import Config
from src.core.behave.scenario_data import ScenarioData
from hooks.resources.registry import ResourceRegistry
from hooks.tag_router import handle_before_tag, handle_after_tag


def before_all(context: Any) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    context.config_obj = Config.load(getattr(context.config, "userdata", {}))
    context.resources = ResourceRegistry()


def before_scenario(context: Any, scenario: Any) -> None:
    # fresh per-scenario shared data with legacy compatibility
    shared_data = ScenarioData._fresh_template()
    context.shared_data = shared_data
    context.data = ScenarioData(context, shared_data)
    context.http_state = context.data.api_state  # backward compatibility for old steps
    context.state = context.data.api_state
    context.ui = getattr(context, "ui", {})
    context.resources.begin_scenario()


def after_scenario(context: Any, scenario: Any) -> None:
    context.resources.teardown_scenario()


def after_all(context: Any) -> None:
    # global teardown handled per scenario; nothing extra for now
    pass


def before_tag(context: Any, tag: str) -> None:
    handle_before_tag(context, tag)


def after_tag(context: Any, tag: str) -> None:
    handle_after_tag(context, tag)
