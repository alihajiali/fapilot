from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass


class MigrationBackend(ABC):
    @abstractmethod
    def init(self) -> None: ...

    @abstractmethod
    def makemigrations(self, name: str | None = None) -> None: ...

    @abstractmethod
    def migrate(self) -> None: ...


@dataclass(slots=True)
class AerichMigrationBackend(MigrationBackend):
    config: str = "pyproject.toml"
    app: str = "models"
    tortoise_config_path: str = "config.database.TORTOISE_ORM"

    def init(self) -> None:
        self._run("init", "-t", self.tortoise_config_path)

    def makemigrations(self, name: str | None = None) -> None:
        args = ["migrate"]
        if name:
            args.extend(["--name", name])
        self._run(*args)

    def migrate(self) -> None:
        self._run("upgrade")

    def _run(self, *args: str) -> None:
        subprocess.run(
            ["aerich", "-c", self.config, "--app", self.app, *args],
            check=True,
        )

