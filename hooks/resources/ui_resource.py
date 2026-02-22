from __future__ import annotations

from dataclasses import dataclass

from hooks.resources.registry import ResourceRegistry


class DummyDriver:
    """Placeholder UI driver; replace with real webdriver as needed."""

    def __init__(self) -> None:
        self.started = True

    def quit(self) -> None:
        self.started = False


@dataclass
class UiRuntime:
    driver: any

    def close(self) -> None:
        drv = getattr(self, "driver", None)
        if drv and hasattr(drv, "quit"):
            drv.quit()


def ensure_ui(context) -> UiRuntime:
    registry: ResourceRegistry = context.resources
    if registry.has("ui"):
        runtime: UiRuntime = registry.get("ui")
        registry.mark_enabled("ui")
        context.ui = {"driver": runtime.driver}
        context.driver = runtime.driver
        return runtime

    driver = DummyDriver()
    runtime = UiRuntime(driver=driver)
    registry.set("ui", runtime)
    registry.mark_enabled("ui")
    context.ui = {"driver": driver}
    context.driver = driver
    return runtime

__all__ = ["ensure_ui", "UiRuntime", "DummyDriver"]
