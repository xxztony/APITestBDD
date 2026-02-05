from __future__ import annotations

import logging
import os
import sys
from typing import Any

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config.config import Config
from src.core.db.db_client import DbClient
from src.core.http.http_client import HttpClient
from src.core.messaging.kafka_client import KafkaClient
from src.core.security.token_manager import TokenManager


def before_all(context: Any) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    context.config_obj = Config.load(getattr(context.config, "userdata", {}))

    context.token_manager = TokenManager()

    context.http_client_factory = None
    context.kafka_factory = None
    context.db_factory = None

    context.clients = {}
    context.system_factories = {}
    context.client_payloads = {}


def before_scenario(context: Any, scenario: Any) -> None:
    context.http_state = {}
    context.state = context.http_state
    context.kafka_client = None
    context.systems = {}

    tags = set(getattr(scenario, "tags", [])) | set(getattr(scenario.feature, "tags", []))
    if "api" not in tags:
        return

    if "crds" in tags:
        from src.clients.crds.user_client import CrdsUserClient
        from src.payloads.crds.create_user import CreateUserRequest
        from src.systems.crds.user import CRDSUser

        base_url = context.config_obj.get("crds.http.base_url")
        if not base_url:
            raise ValueError("Missing config: crds.http.base_url (set via userdata or E2E__CRDS__HTTP__BASE_URL)")
        context.http_client = HttpClient(base_url=base_url, token_manager=context.token_manager, timeout=10.0)

        bootstrap_servers = context.config_obj.get("crds.kafka.bootstrap_servers")
        if bootstrap_servers:
            context.kafka_client = KafkaClient(
                bootstrap_servers=bootstrap_servers,
                scenario_id=str(scenario.name),
                group_prefix="e2e",
            )
        else:
            logging.getLogger(__name__).warning("Kafka config missing: crds.kafka.bootstrap_servers")

        db_conn_str = context.config_obj.get("crds.db.connection_string")
        if db_conn_str:
            context.db_client = DbClient(db_conn_str, timeout=10)
        else:
            context.db_client = None
            logging.getLogger(__name__).warning("DB config missing: crds.db.connection_string")

        context.clients["crds_user"] = CrdsUserClient(context.http_client)
        context.system_factories["crds_user"] = lambda ctx: CRDSUser(ctx)
        context.client_payloads["crds_user.create_user"] = CreateUserRequest

        context.systems = {name: factory(context) for name, factory in context.system_factories.items()}


def after_scenario(context: Any, scenario: Any) -> None:
    if context.kafka_client:
        context.kafka_client.close()


def after_all(context: Any) -> None:
    if getattr(context, "db_client", None):
        context.db_client.close()
