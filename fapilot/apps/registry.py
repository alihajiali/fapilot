from __future__ import annotations

from collections.abc import Iterable
from importlib import import_module

from fapilot.apps.config import AppConfig


class AppRegistry:
    def __init__(self) -> None:
        self._apps: dict[str, AppConfig] = {}
        self.ready = False

    def populate(self, installed_apps: Iterable[str]) -> None:
        if self.ready:
            return
        for dotted_path in installed_apps:
            app_config = self._load_config(dotted_path)
            label = app_config.app_label
            if label in self._apps:
                raise RuntimeError(f"Duplicate app label: {label}")
            self._apps[label] = app_config
        for app_config in self._apps.values():
            app_config.ready()
        self.ready = True

    def get_app(self, label: str) -> AppConfig:
        return self._apps[label]

    def get_apps(self) -> list[AppConfig]:
        return list(self._apps.values())

    def _load_config(self, dotted_path: str) -> AppConfig:
        module_path, _, class_name = dotted_path.rpartition(".")
        if not module_path:
            module_path = f"{dotted_path}.apps"
            class_name = "Config"
        module = import_module(module_path)
        config_cls = getattr(module, class_name)
        config = config_cls()
        if not isinstance(config, AppConfig):
            raise TypeError(f"{dotted_path} must instantiate fapilot.apps.AppConfig")
        return config
