import asyncio
import os
from uuid import uuid4

import pytest
from pydantic import ValidationError
from tortoise import Tortoise

from fapilot.cache import CacheHandler
from fapilot.cache.backends.db import DatabaseCache
from fapilot.cache.backends.dummy import DummyCache
from fapilot.cache.backends.filebased import FileBasedCache
from fapilot.cache.backends.locmem import LocMemCache
from fapilot.conf import FapilotSettings
from fapilot.conf.settings import CacheSettings


@pytest.fixture(params=["locmem", "file", "db", "redis", "pymemcache", "pylibmc"])
async def backend(request, tmp_path):
    kind = request.param
    params = {"KEY_PREFIX": uuid4().hex, "TIMEOUT": 60}
    if kind == "locmem":
        instance = LocMemCache(uuid4().hex, params)
    elif kind == "file":
        instance = FileBasedCache(str(tmp_path / "cache"), params)
    elif kind == "db":
        await Tortoise.init(
            config={
                "connections": {"default": f"sqlite://{tmp_path / 'cache.sqlite3'}"},
                "apps": {"models": {"models": ["aerich.models"]}},
            }
        )
        instance = DatabaseCache("cache_entries", params)
        await instance.create_table()
    elif kind == "redis":
        url = os.getenv("FAPILOT_TEST_REDIS_URL")
        if not url:
            pytest.skip("Set FAPILOT_TEST_REDIS_URL to an isolated test Redis database")
        pytest.importorskip("redis")
        from fapilot.cache.backends.redis import RedisCache

        instance = RedisCache(url, params)
    else:
        server = os.getenv("FAPILOT_TEST_MEMCACHED")
        if not server:
            pytest.skip("Set FAPILOT_TEST_MEMCACHED to an isolated test Memcached server")
        pytest.importorskip(kind)
        from fapilot.cache.backends.memcached import PyLibMCCache, PyMemcacheCache

        cls = PyMemcacheCache if kind == "pymemcache" else PyLibMCCache
        instance = cls(server, params)
    try:
        yield instance
    finally:
        await instance.clear()
        await instance.close()
        if kind == "db":
            await Tortoise.close_connections()


@pytest.mark.anyio
async def test_cache_values_bulk_and_isolation(backend):
    assert await backend.get("missing", "fallback") == "fallback"
    data = {"none": None, "zero": 0, "false": False, "bytes": b"123", "list": [1, "two"]}
    assert await backend.set_many(data) == []
    assert await backend.get_many([*data, "missing"]) == data
    assert await backend.has_key("none")
    assert not await backend.add("none", "replacement")
    assert await backend.add("new", {"a": 1})
    assert await backend.get("new") == {"a": 1}
    assert await backend.set("new", "other-version", version=2)
    assert await backend.get("new", version=2) == "other-version"
    assert await backend.get("new") == {"a": 1}
    await backend.delete_many(data)
    assert await backend.get_many(data) == {}
    assert await backend.delete("new")
    assert not await backend.delete("new")
    await backend.aset("async-alias", "works")
    assert await backend.aget("async-alias") == "works"


@pytest.mark.anyio
async def test_timeout_touch_and_versions(backend):
    await backend.set("instant", 1, timeout=0)
    assert not await backend.has_key("instant")
    await backend.set("forever", 2, timeout=None)
    assert await backend.touch("forever", timeout=None)
    assert await backend.get("forever") == 2
    assert await backend.touch("forever", timeout=0)
    assert not await backend.has_key("forever")
    assert not await backend.touch("absent")
    await backend.set("versioned", 42)
    assert await backend.incr_version("versioned") == 2
    assert await backend.get("versioned") is None
    assert await backend.get("versioned", version=2) == 42
    assert await backend.decr_version("versioned", version=2) == 1
    with pytest.raises(ValueError):
        await backend.incr_version("absent")


@pytest.mark.anyio
async def test_counters_and_get_or_set(backend):
    await backend.set("counter", 10)
    assert await backend.incr("counter", 2) == 12
    assert await backend.decr("counter", 3) == 9
    with pytest.raises(ValueError):
        await backend.incr("missing")
    await asyncio.gather(*(backend.incr("counter") for _ in range(10)))
    assert await backend.get("counter") == 19
    calls = []

    async def calculate():
        calls.append(True)
        return {"calculated": True}

    assert await backend.get_or_set("computed", calculate) == {"calculated": True}
    assert await backend.get_or_set("computed", calculate) == {"calculated": True}
    assert calls == [True]
    await backend.set("already-none", None)
    assert await backend.get_or_set("already-none", calculate) is None
    assert calls == [True]


@pytest.mark.anyio
async def test_local_serialization_expiry_and_capacity(monkeypatch, tmp_path):
    now = [1000.0]
    monkeypatch.setattr("time.time", lambda: now[0])
    for backend in [
        LocMemCache(uuid4().hex, {"TIMEOUT": 5}),
        FileBasedCache(str(tmp_path / "cache"), {"TIMEOUT": 5}),
    ]:
        original = [1]
        await backend.set("key", original)
        original.append(2)
        assert await backend.get("key") == [1]
        now[0] += 6
        assert await backend.get("key") is None
        assert await backend.add("key", "replacement")
        await backend.close()
    small = LocMemCache(uuid4().hex, {"OPTIONS": {"MAX_ENTRIES": 2, "CULL_FREQUENCY": 0}})
    await small.set_many({"one": 1, "two": 2})
    await small.set("three", 3)
    assert await small.get_many(["one", "two", "three"]) == {"three": 3}


@pytest.mark.anyio
async def test_dummy_cache_never_stores():
    backend = DummyCache("", {})
    assert await backend.set("key", 1)
    assert await backend.add("key", 2)
    assert await backend.get("key", "missing") == "missing"
    assert await backend.get_or_set("key", lambda: 3) == 3
    assert not await backend.touch("key")
    assert not await backend.delete("key")
    assert await backend.clear()
    with pytest.raises(ValueError):
        await backend.incr("key")


@pytest.mark.anyio
async def test_aliases_django_paths_and_custom_key_function():
    location = uuid4().hex
    settings = FapilotSettings(
        CACHES={
            "default": CacheSettings(LOCATION=location),
            "other": CacheSettings(
                BACKEND="django.core.cache.backends.locmem.LocMemCache",
                LOCATION=location,
                KEY_PREFIX="isolated",
            ),
            "custom": CacheSettings(LOCATION=location, KEY_FUNCTION="tests.test_cache.cache_key"),
        }
    )
    handler = CacheHandler(settings)
    assert handler["default"] is handler["default"]
    await handler["default"].set("same", 1)
    assert await handler["other"].get("same") is None
    assert handler["custom"].make_key("one") == "custom:one:1"
    with pytest.raises(KeyError, match="Unknown cache alias"):
        handler["missing"]
    first = handler["default"]
    await handler.close_all()
    assert handler["default"] is not first
    assert await handler["default"].get("same") == 1
    await handler["default"].clear()


def cache_key(key, prefix, version):
    return f"custom:{key}:{version}"


def test_cache_settings_from_environment(monkeypatch):
    monkeypatch.setenv("CACHES__default__TIMEOUT", "25")
    monkeypatch.setenv("CACHES__default__BACKEND", "fapilot.cache.backends.dummy.DummyCache")
    settings = FapilotSettings()
    assert settings.CACHES["default"].TIMEOUT == 25
    assert settings.CACHES["default"].BACKEND.endswith(".DummyCache")
    monkeypatch.delenv("CACHES__default__TIMEOUT")
    monkeypatch.delenv("CACHES__default__BACKEND")
    with pytest.raises(ValidationError, match="default alias"):
        FapilotSettings.model_validate({"CACHES": {"other": CacheSettings()}})
    with pytest.raises(ValueError, match="simple SQL table name"):
        DatabaseCache("table; DROP TABLE users", {})


@pytest.mark.anyio
async def test_cache_table_on_secondary_connection(tmp_path):
    from tortoise import connections

    await Tortoise.init(
        config={
            "connections": {
                "default": f"sqlite://{tmp_path / 'main.sqlite3'}",
                "cache_db": f"sqlite://{tmp_path / 'cache.sqlite3'}",
            },
            "apps": {"models": {"models": ["aerich.models"]}},
        }
    )
    handler = CacheHandler(
        FapilotSettings(
            CACHES={
                "default": CacheSettings(),
                "database": CacheSettings(
                    BACKEND="fapilot.cache.backends.db.DatabaseCache",
                    LOCATION="entries",
                    OPTIONS={"CONNECTION": "cache_db"},
                ),
            }
        )
    )
    try:
        await handler.create_tables()
        await handler.create_tables()  # Existing data/schema is retained.
        await handler["database"].set("item", "secondary")
        rows = await connections.get("cache_db").execute_query_dict("SELECT * FROM entries")
        assert len(rows) == 1
        rows = await connections.get("default").execute_query_dict(
            "SELECT name FROM sqlite_master WHERE name = 'entries'"
        )
        assert rows == []
    finally:
        await handler.close_all()
        await Tortoise.close_connections()


def test_cache_available_in_http_requests(tmp_path):
    from fastapi import Request
    from fastapi.testclient import TestClient

    from fapilot import create_app

    app = create_app(
        FapilotSettings(
            DATABASE_URL=f"sqlite://{tmp_path / 'app.sqlite3'}",
            INSTALLED_APPS=[],
            CACHES={"default": CacheSettings(LOCATION=uuid4().hex)},
        )
    )

    @app.get("/cached")
    async def cached(request: Request):
        backend = request.app.state.caches["default"]
        await backend.add("visits", 0)
        return {"visits": await backend.incr("visits")}

    with TestClient(app) as client:
        assert client.get("/cached").json() == {"visits": 1}
        assert client.get("/cached").json() == {"visits": 2}


@pytest.mark.anyio
async def test_expiry_and_atomic_add(backend):
    await backend.set("expires", "value", timeout=1)
    assert await backend.get("expires") == "value"
    await asyncio.sleep(1.1)
    assert await backend.get("expires", "missing") == "missing"
    results = await asyncio.gather(*(backend.add("race", index) for index in range(10)))
    assert results.count(True) == 1
    assert await backend.get("race") in range(10)
    assert not await backend.add("race", "never", timeout=0)
    await backend.set("long-lived", "yes", timeout=60 * 60 * 24 * 40)
    assert await backend.get("long-lived") == "yes"


@pytest.mark.anyio
async def test_cleanup_attempts_every_backend(monkeypatch):
    handler = CacheHandler(
        FapilotSettings(
            CACHES={
                "default": CacheSettings(LOCATION=uuid4().hex),
                "second": CacheSettings(LOCATION=uuid4().hex),
            }
        )
    )
    closed = []

    async def broken_close():
        closed.append("first")
        raise RuntimeError("close failure")

    async def good_close():
        closed.append("second")

    monkeypatch.setattr(handler["default"], "close", broken_close)
    monkeypatch.setattr(handler["second"], "close", good_close)
    with pytest.raises(ExceptionGroup, match="Cache cleanup failed"):
        await handler.close_all()
    assert closed == ["first", "second"]


def test_cache_cleanup_after_shutdown_receiver_error(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from fapilot import Fapilot

    framework = Fapilot(FapilotSettings(DATABASE_URL=f"sqlite://{tmp_path / 'lifecycle.sqlite3'}"))
    app = framework.create_fastapi()
    closed = []

    async def close():
        closed.append(True)

    async def fail(app):
        raise RuntimeError("shutdown failed")

    monkeypatch.setattr(framework.caches["default"], "close", close)
    framework.events.connect("shutdown", fail)
    with pytest.raises(RuntimeError, match="shutdown failed"), TestClient(app):
        pass
    assert closed == [True]


def test_createcachetable_cli(tmp_path):
    import subprocess
    import sys

    config = tmp_path / "config"
    config.mkdir()
    (config / "__init__.py").write_text("")
    (config / "settings.py").write_text(
        'DATABASE_URL = "sqlite://cache.sqlite3"\n'
        'CACHES = {"default": {"BACKEND": "fapilot.cache.backends.db.DatabaseCache", '
        '"LOCATION": "test_entries"}}\n'
    )
    command = [sys.executable, "-c", "from fapilot.cli import main; main()", "createcachetable"]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    import sqlite3

    with sqlite3.connect(tmp_path / "cache.sqlite3") as connection:
        assert connection.execute("SELECT COUNT(*) FROM test_entries").fetchone() == (0,)
