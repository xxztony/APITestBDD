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
from src.core.security.token_manager import TokenManager


def before_all(context: Any) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    context.config_obj = Config.load(getattr(context.config, "userdata", {}))
    context.token_manager = TokenManager()


def before_scenario(context: Any, scenario: Any) -> None:
    # fresh per-scenario data (API only)
    context.shared_data = {}
    context.http_data = ScenarioData(context)


def after_scenario(context: Any, scenario: Any) -> None:
    pass


def after_all(context: Any) -> None:
    if getattr(context, "db_client", None):
        context.db_client.close()
