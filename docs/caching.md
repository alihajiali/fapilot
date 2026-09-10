# Caching

[Documentation index](index.md)

Fapilot supports the same built-in cache backend families as
[Django's cache framework](https://docs.djangoproject.com/en/6.0/topics/cache/):
local memory, filesystem, database, Redis, Memcached through pymemcache or pylibmc,
and dummy caching. These are native Fapilot implementations; Django is not required.
All operations are asynchronous. Template fragment caching is not included.

## Quick start

The default cache is process-local memory with a 300-second timeout. In an endpoint,
use the handler associated with that application:

```python
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/visits")
async def visits(request: Request):
    cache = request.app.state.caches["default"]
    await cache.add("visits", 0, timeout=3600)
    return {"visits": await cache.incr("visits")}
```

`request.app.state.cache` is a convenience reference to the default backend.
`request.app.state.fapilot.caches` exposes the same handler. Backend connections are
closed during lifespan cleanup, including when startup/shutdown receivers fail.
Closing releases resources and does not clear cached data.

For scripts, use `CacheHandler(settings)` or the global `cache` and `caches` objects:

```python
import asyncio
from fapilot.cache import cache, caches


async def main():
    try:
        await cache.set("answer", 42, timeout=60)
        assert await cache.get("answer") == 42
    finally:
        await caches.close_all()


if __name__ == "__main__":
    asyncio.run(main())
```

The global handler reads `get_settings()` lazily. It is independent of app-local
handlers; prefer application state in request code when using explicit app settings.
Close the global handler yourself before shutting down its event loop. Do not share
one Redis-backed handler across independent event loops. `close_all()` drops backend
instances so later accesses construct fresh clients.

## Configuration

Use `CACHES` in `config/settings.py`:

```python
CACHES = {
    "default": {
        "BACKEND": "fapilot.cache.backends.locmem.LocMemCache",
        "LOCATION": "myproject-default",
        "TIMEOUT": 300,
        "KEY_PREFIX": "myproject",
        "VERSION": 1,
        "OPTIONS": {"MAX_ENTRIES": 1000, "CULL_FREQUENCY": 3},
    },
    "reports": {
        "BACKEND": "fapilot.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/tmp/myproject-report-cache",
        "TIMEOUT": 600,
    },
}
```

Retrieve a named backend with `handler["reports"]`. A `default` alias is required;
unknown aliases raise `KeyError`. Unknown configuration fields are rejected.
Each alias is instantiated once per handler. Backends are created lazily, except
an app's default cache, which is resolved during app creation.

The corresponding built-in `django.core.cache.backends.*` class paths are accepted
as aliases for the Fapilot classes. This is configuration familiarity, not a promise
of Django storage-format compatibility or support for arbitrary Django plugins.

| Key | Default | Purpose |
| --- | --- | --- |
| `BACKEND` | `fapilot.cache.backends.locmem.LocMemCache` | Backend class import path |
| `LOCATION` | `fapilot-default` | Store name, directory, table, server, or list of servers |
| `TIMEOUT` | `300` | Default entry lifetime in seconds; `None` never expires |
| `OPTIONS` | `{}` | Backend-specific settings or client constructor options |
| `KEY_PREFIX` | `""` | Prefix separating application key names |
| `VERSION` | `1` | Default key version |
| `KEY_FUNCTION` | `None` | Callable or import path for `(key, key_prefix, version) -> str` |

Environment configuration supports JSON and nested variables, for example
`CACHES__default__TIMEOUT=60`. Explicit Python settings take precedence for the same
keys; nested mappings may merge with environment values through Pydantic Settings.
For typed construction, import `CacheSettings` from `fapilot.conf.settings` and use
`FapilotSettings(CACHES={"default": CacheSettings(...)})`.

## Built-in backends

### Local memory

Backend: `fapilot.cache.backends.locmem.LocMemCache`.
`LOCATION` identifies a process-wide store. Handlers using the same location share
that store; different worker processes do not. Operations are thread-safe and counters
and `add` are atomic within the process. Values are serialized so modifying a returned
list or dictionary does not modify the cached copy.

`OPTIONS.MAX_ENTRIES` defaults to 300. `CULL_FREQUENCY` defaults to 3 and evicts roughly
one third of entries when capacity is reached; zero clears the store when it fills.
Eviction uses least-recently-used order. These limits are per store, not per prefix.

### Filesystem

Backend: `fapilot.cache.backends.filebased.FileBasedCache`.
`LOCATION` is a dedicated writable directory, created when writing the first entry.
Keys are hashed into filenames; writes use temporary files and atomic replacement.
Blocking file work runs in worker threads. The same capacity/culling options are
supported, but eviction order is not LRU.

Files persist across application restarts. Locks coordinate instances within one
process; multi-process read/modify/write operations such as counters and `add` are not
atomic. Use a network cache when cross-worker atomicity matters.

### Database

Backend: `fapilot.cache.backends.db.DatabaseCache`.
`LOCATION` is a table name containing only letters, digits, and underscores, starting
with a letter or underscore. SQLite, PostgreSQL, and MySQL Tortoise connections are
supported. The cache table is separate from business model groups and Aerich models.

```python
DATABASES = {"cache_db": "sqlite://cache.sqlite3"}
CACHES = {
    "default": {
        "BACKEND": "fapilot.cache.backends.db.DatabaseCache",
        "LOCATION": "application_cache",
        "TIMEOUT": 300,
        "OPTIONS": {
            "CONNECTION": "cache_db",
            "MAX_ENTRIES": 1000,
            "CULL_FREQUENCY": 3,
        },
    },
}
```

Create missing cache tables explicitly before using the cache:

```bash
fapilot createcachetable
# Or just one named database-cache alias:
fapilot createcachetable --cache default
```

The command loads `config.settings` from the project root, opens configured ORM
connections, creates tables, and closes connections. It does not run business model
migrations or change an existing table. Provision database servers/databases separately.
Applications using the backend need their normal ORM lifespan initialized; scripts
can initialize Tortoise and then call `await handler.create_tables()`.

`OPTIONS.CONNECTION` defaults to `default`; it refers to the effective `DATABASES`
map (including the legacy `DATABASE_URL` fallback). Expired rows are invisible to
reads and are removed when adding or setting entries. Capacity culling is opportunistic,
not a strict global size bound under concurrent writers. Counters use optimistic
compare-and-swap, preserve expiration, and raise if their retry limit is exhausted.
Cache keys must fit the table's 255-character key column.

### Redis

Backend: `fapilot.cache.backends.redis.RedisCache`.
Install the optional client:

```bash
python -m pip install 'fapilot[cache-redis]'
```

```python
CACHES = {
    "default": {
        "BACKEND": "fapilot.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {"socket_connect_timeout": 2, "socket_timeout": 2},
    },
}
```

URLs can use Redis-supported TCP, TLS (`rediss://`), or Unix-socket schemes.
A list, semicolon-separated string, or comma-separated string of URLs configures
a leader followed by read replicas: writes use the first server, reads randomly use
the others. Configure replication yourself. Replica lag can produce stale reads;
use one server when immediate read-after-write consistency is required.

`OPTIONS` is passed to `redis.asyncio.Redis.from_url`. Response decoding must remain
disabled because values are binary. This implementation does not consume Django-specific
serializer, parser, or pool import-path options. Redis performs native atomic `add`
and integer counters. Expiration uses millisecond resolution.

### Memcached with pymemcache

Backend: `fapilot.cache.backends.memcached.PyMemcacheCache`.

```bash
python -m pip install 'fapilot[cache-pymemcache]'
```

```python
CACHES = {
    "default": {
        "BACKEND": "fapilot.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": ["127.0.0.1:11211"],
        "OPTIONS": {"connect_timeout": 2, "timeout": 2, "no_delay": True},
    },
}
```

Uses pymemcache's `HashClient`; `OPTIONS` is forwarded to its constructor. Server
locations also accept a delimited string or `unix:/path/to/socket`. Unicode keys are
enabled, and `default_noreply=False` is required to report mutation results correctly.
Blocking client calls run in worker threads and are serialized per backend instance.

### Memcached with pylibmc

Backend: `fapilot.cache.backends.memcached.PyLibMCCache`.

```bash
python -m pip install 'fapilot[cache-pylibmc]'
```

This client may require platform build tools and libmemcached development libraries.
`LOCATION` accepts the same forms as the pymemcache backend. `OPTIONS` is passed to
`pylibmc.Client`, for example `{"binary": True, "behaviors": {"tcp_nodelay": True}}`.
Calls run off the event loop with a per-instance client lock.

Both Memcached backends enforce the 250-byte key limit and reject whitespace/control
characters after prefix/version processing. Their native counters are unsigned:
decrementing below zero yields zero. Expiry has whole-second precision; lifetimes
above 30 days are converted to absolute timestamps as required by Memcached.

To install all network-client extras together, use `pip install 'fapilot[cache]'`.
No cache server is installed or started by these Python extras.

### Dummy

Backend: `fapilot.cache.backends.dummy.DummyCache`.
Writes report success but nothing is stored; reads always miss. This is useful for
disabling caching without changing application code. `get_or_set` still computes
its default. `touch` and `delete` return false; counters raise for missing keys.

## Operations

All methods below must be awaited. Django-style async spellings such as `aget`,
`aset`, and `aget_many` are aliases of the corresponding methods.

| Operation | Result / behavior |
| --- | --- |
| `get(key, default=None, version=None)` | Value, or supplied default on miss |
| `set(key, value, timeout=DEFAULT_TIMEOUT, version=None)` | Boolean success |
| `add(key, value, timeout=DEFAULT_TIMEOUT, version=None)` | Store only if absent; boolean success |
| `get_or_set(key, default, timeout=DEFAULT_TIMEOUT, version=None)` | Value; default can be a value, sync callable, or async callable |
| `get_many(keys, version=None)` | Dictionary containing found keys only |
| `set_many(mapping, timeout=DEFAULT_TIMEOUT, version=None)` | List of keys whose write returned failure |
| `delete(key, version=None)` | Boolean indicating whether a key was removed |
| `delete_many(keys, version=None)` | Deletes supplied keys; no result value |
| `has_key(key, version=None)` | Membership test that distinguishes cached `None` from a miss |
| `touch(key, timeout=DEFAULT_TIMEOUT, version=None)` | Change expiry without changing value; false if absent |
| `incr(key, delta=1, version=None)` / `decr(...)` | Integer result; missing keys raise `ValueError` |
| `incr_version(key, delta=1, version=None)` / `decr_version(...)` | Moves value to a new key version; resets its TTL to the default |
| `clear()` | Clears the underlying cache storage, not just this key prefix |
| `close()` | Releases backend resources without deleting entries |

`version` arguments are keyword-only. Omitted timeouts use the configured default;
`None` means no expiry, and zero or negative timeouts mean immediate expiry.
Timeouts must be finite. Counters require integer values and integer deltas; backend
errors for unsupported values or network failures propagate.

The default key is `KEY_PREFIX:VERSION:key`. A custom `KEY_FUNCTION` changes this
composition and must return a string. Version changes are not atomic across workers.
`get_or_set` uses `add` to avoid overwriting another writer's value, but concurrent
callers can still evaluate the factory more than once. It is not a distributed lock.
Bulk methods currently perform individual operations; they do not imply a transaction.

## Serialization and cache boundaries

Values must be pickle-serializable Python objects; plain integer encoding also allows
server-side counters. Cached `None`, `False`, bytes, and empty collections are distinct
from a miss. Do not place database model instances or active connections in caches;
store explicit data structures instead.

Only trusted application processes should be able to write to the cache. Loading
malicious pickle data can execute code. Keep file caches outside web-served/upload
directories, restrict directory permissions, and protect network caches with appropriate
network access and authentication. Never use cached data as the sole source of truth.

`clear()` affects every prefix/version in the backend's store: the local-memory location,
all `.cache` files in the configured directory, the entire configured cache table,
the selected Redis database (`FLUSHDB`), or all configured Memcached servers. Use dedicated
storage if another application shares the service; use `delete_many` for targeted removal.

## Custom backends

Subclass `fapilot.cache.BaseCache` and configure its full class path in `BACKEND`.
The constructor receives `(location, params)`. Implement async `_get`, `_set`, `_add`,
`_delete`, `_touch`, `_incr`, and `clear`; override `close` for resource cleanup.
Raw getters return bytes or `None`; raw writers receive serialized bytes and a resolved
TTL in seconds (or `None`). The base class supplies key composition and high-level methods.
A custom database subclass can inherit `DatabaseCache.create_table()` and participates
in `createcachetable`. Arbitrary synchronous Django third-party backends need an adapter
to this async contract; they are not automatically imported as compatible implementations.

## Testing

`tests/test_cache.py` covers all backend families. Local/file/SQLite/dummy tests need
no external service. To run network tests, install the optional client extras and set
`FAPILOT_TEST_REDIS_URL` and `FAPILOT_TEST_MEMCACHED` to disposable dedicated services.
Tests call `clear()` during cleanup; never point them at application caches. CI provisions
isolated Redis and Memcached services and installs both client bindings.
