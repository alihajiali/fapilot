from __future__ import annotations

from collections.abc import Callable


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, Callable[..., None]] = {}

    def register(self, name: str, command: Callable[..., None]) -> None:
        self._commands[name] = command

    def get(self, name: str) -> Callable[..., None]:
        return self._commands[name]

