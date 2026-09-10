from __future__ import annotations

import base64
import re
import time
from typing import Any

from tortoise import connections

from fapilot.cache.backends.base import BaseCache, deserialize, serialize


class DatabaseCache(BaseCache):
    """Cache table on a configured Tortoise SQLite, PostgreSQL, or MySQL connection."""

    def __init__(self, location: str | list[str], params: dict[str, Any]) -> None:
        super().__init__(location, params)
        if not isinstance(location, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", location):
            raise ValueError("Database cache LOCATION must be a simple SQL table name")
        self.table = location
        self.connection = self.options.get("CONNECTION", "default")
        self.max_entries = int(self.options.get("MAX_ENTRIES", 300))
        self.cull_frequency = int(self.options.get("CULL_FREQUENCY", 3))
        if self.max_entries < 1 or self.cull_frequency < 0:
            raise ValueError("Invalid cache capacity or cull frequency")

    def _sql(self, query: str) -> str:
        dialect = connections.get(self.connection).capabilities.dialect
        if dialect == "postgres":
            parts = query.split("?")
            return "".join(
                part + (f"${i + 1}" if i < len(parts) - 1 else "") for i, part in enumerate(parts)
            )
        if dialect == "mysql":
            return query.replace("?", "%s").replace('"', "`")
        if dialect != "sqlite":
            raise ValueError("Database cache supports SQLite, PostgreSQL, and MySQL")
        return query

    async def _query(self, query: str, values: list[Any] | None = None) -> tuple[int, Any]:
        return await connections.get(self.connection).execute_query(self._sql(query), values or [])

    async def create_table(self) -> None:
        mysql = connections.get(self.connection).capabilities.dialect == "mysql"
        key_type = (
            "VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin" if mysql else "VARCHAR(255)"
        )
        value_type = "LONGTEXT CHARACTER SET ascii COLLATE ascii_bin" if mysql else "TEXT"
        await self._query(
            f'CREATE TABLE IF NOT EXISTS "{self.table}" ('
            f"cache_key {key_type} PRIMARY KEY, value {value_type} NOT NULL, "
            "expires DOUBLE PRECISION)"
        )

    async def _row(self, key: str) -> Any:
        _, rows = await self._query(
            f'SELECT value, expires FROM "{self.table}" WHERE cache_key = ? '
            "AND (expires IS NULL OR expires > ?)",
            [key, time.time()],
        )
        return rows[0] if rows else None

    async def _get(self, key: str) -> bytes | None:
        row = await self._row(key)
        return None if row is None else base64.b64decode(row["value"])

    async def _cull(self) -> None:
        await self._query(f'DELETE FROM "{self.table}" WHERE expires <= ?', [time.time()])
        _, rows = await self._query(f'SELECT COUNT(*) AS total FROM "{self.table}"')
        count = rows[0]["total"]
        if count < self.max_entries:
            return
        if self.cull_frequency == 0:
            await self.clear()
            return
        _, rows = await self._query(
            f'SELECT cache_key FROM "{self.table}" ORDER BY expires LIMIT ?',
            [max(1, count // self.cull_frequency)],
        )
        for row in rows:
            await self._delete(row["cache_key"])

    async def _set(self, key: str, value: bytes, timeout: float | None) -> bool:
        if timeout is not None and timeout <= 0:
            await self._delete(key)
            return True
        await self._cull()
        expires = None if timeout is None else time.time() + timeout
        data = base64.b64encode(value).decode()
        sql = f'INSERT INTO "{self.table}" (cache_key, value, expires) VALUES (?, ?, ?) '
        if connections.get(self.connection).capabilities.dialect == "mysql":
            sql += "ON DUPLICATE KEY UPDATE value = VALUES(value), expires = VALUES(expires)"
        else:
            sql += "ON CONFLICT (cache_key) DO UPDATE SET value = excluded.value, "
            sql += "expires = excluded.expires"
        await self._query(sql, [key, data, expires])
        return True

    async def _add(self, key: str, value: bytes, timeout: float | None) -> bool:
        # Avoid evicting an existing key before deciding whether add can succeed.
        if await self._get(key) is not None:
            return False
        if timeout is not None and timeout <= 0:
            return True
        await self._cull()
        expires = None if timeout is None else time.time() + timeout
        data = base64.b64encode(value).decode()
        sql = f'INSERT INTO "{self.table}" (cache_key, value, expires) VALUES (?, ?, ?)'
        if connections.get(self.connection).capabilities.dialect == "mysql":
            sql = sql.replace("INSERT INTO", "INSERT IGNORE INTO")
        else:
            sql += " ON CONFLICT (cache_key) DO NOTHING"
        count, _ = await self._query(sql, [key, data, expires])
        return count > 0

    async def _delete(self, key: str) -> bool:
        count, _ = await self._query(f'DELETE FROM "{self.table}" WHERE cache_key = ?', [key])
        return count > 0

    async def _touch(self, key: str, timeout: float | None) -> bool:
        expires = None if timeout is None else time.time() + timeout
        count, _ = await self._query(
            f'UPDATE "{self.table}" SET expires = ? WHERE cache_key = ? '
            "AND (expires IS NULL OR expires > ?)",
            [expires, key, time.time()],
        )
        return count > 0

    async def _incr(self, key: str, delta: int) -> int:
        # Optimistic compare-and-swap preserves expiration and concurrent increments.
        for _ in range(100):
            row = await self._row(key)
            if row is None:
                raise ValueError("Cache key does not exist")
            value = deserialize(base64.b64decode(row["value"]))
            if type(value) is not int:
                raise ValueError("Cache value must be an integer")
            if delta == 0:
                return value
            result = value + delta
            count, _ = await self._query(
                f'UPDATE "{self.table}" SET value = ? WHERE cache_key = ? AND value = ? '
                "AND (expires IS NULL OR expires > ?)",
                [base64.b64encode(serialize(result)).decode(), key, row["value"], time.time()],
            )
            if count:
                return result
        raise RuntimeError("Cache counter contention exceeded retry limit")

    async def clear(self) -> bool:
        await self._query(f'DELETE FROM "{self.table}"')
        return True
