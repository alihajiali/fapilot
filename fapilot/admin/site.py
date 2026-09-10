# Embedded HTML keeps complete tags together.
# ruff: noqa: E501
from __future__ import annotations

import csv
import inspect
import io
import json
import secrets
import time
from collections import OrderedDict
from datetime import UTC, date, datetime, timedelta
from importlib import import_module
from typing import Any
from urllib.parse import quote, urlencode

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.routing import APIRoute
from jose import JWTError, jwt
from starlette.responses import HTMLResponse, RedirectResponse, Response
from tortoise import fields
from tortoise.exceptions import IntegrityError, ValidationError
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.transactions import in_transaction

from fapilot.admin import ui
from fapilot.admin.models import AdminLogEntry
from fapilot.admin.options import ModelAdmin


class AdminSite:
    """An isolated model registry and cookie-authenticated administration site.

    authenticate(request, username, password) must return a nonempty staff identifier
    or None. authorize(request, identifier) must recheck active staff access on every
    request. Both callbacks may be async. No authentication backend is enabled by default.
    """

    def __init__(
        self,
        *,
        title: str = "Fapilot",
        authenticate: Any = None,
        authorize: Any = None,
        change_password: Any = None,
    ) -> None:
        self.title = title
        self.authenticate = authenticate
        self.authorize = authorize
        self.change_password = change_password
        self._registry: dict[str, ModelAdmin] = {}
        self._login_attempts: OrderedDict[str, list[float]] = OrderedDict()

    def register(
        self,
        model: type[Model],
        admin_class: type[ModelAdmin] = ModelAdmin,
        *,
        name: str | None = None,
    ) -> type[ModelAdmin]:
        key = name or f"{model.__module__}.{model.__name__}".lower()
        if (
            not key
            or len(key) > 255
            or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_.-" for c in key)
        ):
            raise ValueError("Admin names must use lowercase letters, numbers, dots, - or _")
        if key in self._registry or any(a.model is model for a in self._registry.values()):
            raise ValueError(f"Model already registered: {key}")
        self._registry[key] = admin_class(model)
        self._registry[key].registry_name = key
        return admin_class

    def unregister(self, model: type[Model]) -> None:
        for key, admin in list(self._registry.items()):
            if admin.model is model:
                del self._registry[key]
                return
        raise KeyError(model)

    def autodiscover(self, app_names: list[str], modules: list[str] | None = None) -> None:
        for name in app_names:
            path = f"{name}.admin"
            try:
                import_module(path)
            except ModuleNotFoundError as exc:
                if exc.name != path:
                    raise
        for path in modules or []:
            import_module(path)

    def mount(
        self,
        app: FastAPI,
        *,
        secret_key: str,
        prefix: str = "/admin",
        secure_cookies: bool = True,
        session_seconds: int = 3600,
    ) -> None:
        if not 60 <= session_seconds <= 86400:
            raise ValueError("Admin session_seconds must be between 60 and 86400")
        if len(secret_key) < 32 or secret_key == "change-me":
            raise ValueError("Admin requires a SECRET_KEY of at least 32 characters")
        if not prefix.startswith("/") or prefix == "/" or any(c in prefix for c in '?#{}<>"'):
            raise ValueError("Admin prefix must be a non-root URL path")
        base = prefix.rstrip("/")
        cookie = "fapilot_admin_" + base.strip("/").replace("/", "_")

        class AdminRoute(APIRoute):
            def get_route_handler(self):
                original = super().get_route_handler()

                async def handler(request: Request):
                    try:
                        return await original(request)
                    except HTTPException as exc:
                        payload = await identity(request)
                        title = {
                            400: "Invalid request",
                            403: "Access denied",
                            404: "Not found",
                        }.get(exc.status_code, "Request failed")
                        body = f'<div class="card empty"><h1>{title}</h1><p>{ui.e(exc.detail)}</p><a href="{base}/">Back to overview</a></div>'
                        return await render(request, title, body, payload, exc.status_code)

                return handler

        router = APIRouter(prefix=base, include_in_schema=False, route_class=AdminRoute)

        def sign(subject: str, purpose: str, nonce: str = "", version: str = "") -> str:
            return jwt.encode(
                {
                    "sub": subject,
                    "purpose": purpose,
                    "nonce": nonce,
                    "version": version,
                    "aud": base,
                    "exp": datetime.now(UTC) + timedelta(seconds=session_seconds),
                },
                secret_key,
                algorithm="HS256",
            )

        def decode(value: str, purpose: str) -> dict:
            try:
                payload = jwt.decode(value, secret_key, algorithms=["HS256"], audience=base)
                return payload if payload.get("purpose") == purpose else {}
            except JWTError:
                return {}

        async def invoke(callback: Any, *args: Any) -> Any:
            result = callback(*args)
            return await result if inspect.isawaitable(result) else result

        async def identity(request: Request) -> dict:
            payload = decode(request.cookies.get(cookie, ""), "session")
            if not payload or not self.authorize:
                return {}
            if not await invoke(self.authorize, request, payload["sub"]):
                return {}
            if payload.get("version", "") != getattr(request.state, "admin_session_version", ""):
                return {}
            request.state.admin_user = payload["sub"]
            return payload

        def csrf_check(form: Any, payload: dict) -> None:
            value = str(form.get("_csrf", ""))
            if not value or not secrets.compare_digest(value, payload.get("nonce", "")):
                raise HTTPException(403, "Invalid CSRF token; reload the form")

        async def audit(
            request: Request,
            key: str,
            obj: Model,
            action: str,
            changed_fields: list[str] | None = None,
        ) -> None:
            await AdminLogEntry.create(
                site=base,
                model=key,
                object_id=str(obj.pk),
                actor=request.state.admin_user,
                action=action,
                changed_fields=changed_fields or [],
            )

        async def render(
            request: Request, title: str, body: str, payload: dict, status: int = 200
        ) -> HTMLResponse:
            nav = ""
            for key, admin in self._registry.items():
                if payload and await admin.has_view_permission(request):
                    nav += f'<a href="{base}/{key}/">{ui.e(label(admin))}</a>'
            if payload and self.change_password:
                nav += f'<a href="{base}/password">Change password</a>'
            if request.query_params.get("saved") == "1":
                body = '<p class="notice" role="status">Your changes have been saved.</p>' + body
            response = HTMLResponse(
                ui.page(
                    title,
                    body,
                    base,
                    payload.get("nonce", ""),
                    nav=nav,
                    user=str(getattr(request.state, "admin_staff", payload.get("sub", "")))
                    if payload
                    else "",
                    site_title=self.title,
                ),
                status_code=status,
            )
            response.headers.update(
                {
                    "Cache-Control": "no-store",
                    "X-Content-Type-Options": "nosniff",
                    "Referrer-Policy": "same-origin",
                    "Content-Security-Policy": "default-src 'none'; style-src 'self'; "
                    "script-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
                }
            )
            return response

        @router.get("/assets/{asset}")
        async def asset(asset: str) -> Response:
            if asset == "admin.css":
                return Response(ui.CSS, media_type="text/css")
            if asset == "admin.js":
                return Response(ui.JS, media_type="text/javascript")
            raise HTTPException(404)

        @router.api_route("/login", methods=["GET", "POST"])
        async def login(request: Request) -> Response:
            error = ""
            status = 200
            nonce = secrets.token_urlsafe(32)
            if request.method == "POST":
                form = await request.form()
                csrf_check(form, decode(request.cookies.get(cookie + "_login", ""), "login"))
                address = request.client.host if request.client else "unknown"
                now = time.monotonic()
                attempts = [t for t in self._login_attempts.pop(address, []) if t > now - 300]
                self._login_attempts[address] = attempts
                while len(self._login_attempts) > 10000:
                    self._login_attempts.popitem(last=False)
                if len(attempts) >= 10:
                    return await render(
                        request,
                        "Try again later",
                        '<div class="card"><h1>Too many sign-in attempts</h1>'
                        "<p>Wait five minutes before trying again.</p></div>",
                        {},
                        429,
                    )
                attempts.append(now)
                user = None
                if self.authenticate and self.authorize:
                    user = await invoke(
                        self.authenticate,
                        request,
                        str(form.get("username", "")),
                        str(form.get("password", "")),
                    )
                    if user and not await invoke(self.authorize, request, str(user)):
                        user = None
                if user:
                    self._login_attempts.pop(address, None)
                    response = RedirectResponse(base + "/", status_code=303)
                    response.set_cookie(
                        cookie,
                        sign(
                            str(user),
                            "session",
                            nonce,
                            getattr(request.state, "admin_session_version", ""),
                        ),
                        httponly=True,
                        secure=secure_cookies,
                        samesite="strict",
                        path=base,
                        max_age=session_seconds,
                    )
                    response.delete_cookie(cookie + "_login", path=base)
                    return response
                error = '<p class="error" role="alert">Sign-in failed. Check your credentials and staff access.</p>'
                status = 401
            body = f"""<div class="card"><div class="brand">◈ {ui.e(self.title)}</div>
<h1>Welcome back</h1><p class="muted">Sign in to your administration workspace.</p>{error}
<form method="post">{ui.token(nonce)}<div class="field"><label for="username">Username</label>
<input id="username" name="username" autocomplete="username" required autofocus></div>
<div class="field"><label for="password">Password</label><input id="password" name="password"
type="password" autocomplete="current-password" required></div><button class="primary">Sign in</button></form></div>"""
            response = await render(request, "Sign in", body, {}, status)
            response.set_cookie(
                cookie + "_login",
                sign("login", "login", nonce),
                httponly=True,
                secure=secure_cookies,
                samesite="strict",
                path=base,
                max_age=session_seconds,
            )
            return response

        @router.api_route("/password", methods=["GET", "POST"])
        async def password(request: Request) -> Response:
            payload = await identity(request)
            if not payload:
                return RedirectResponse(base + "/login", status_code=303)
            if self.change_password is None:
                raise HTTPException(404)
            error = ""
            if request.method == "POST":
                form = await request.form()
                csrf_check(form, payload)
                try:
                    new = str(form.get("new_password", ""))
                    if new != str(form.get("confirm_password", "")):
                        raise ValueError("Passwords do not match")
                    if not await invoke(
                        self.change_password, request, str(form.get("old_password", "")), new
                    ):
                        raise ValueError("Incorrect current password")
                    response = RedirectResponse(base + "/login", status_code=303)
                    response.delete_cookie(cookie, path=base)
                    return response
                except ValueError:
                    error = '<p class="error" role="alert">Check your current password and enter matching new passwords of at least 12 characters.</p>'
            body = f'<h1>Change password</h1>{error}<form method="post" class="card">{ui.token(payload["nonce"])}'
            for name, title in (
                ("old_password", "Current password"),
                ("new_password", "New password"),
                ("confirm_password", "Confirm new password"),
            ):
                autocomplete = "current-password" if name == "old_password" else "new-password"
                body += f'<div class="field"><label for="{name}">{title}</label><input id="{name}" name="{name}" type="password" autocomplete="{autocomplete}" required></div>'
            body += '<button class="primary">Change password and sign out</button></form>'
            return await render(request, "Change password", body, payload, 400 if error else 200)

        @router.post("/logout")
        async def logout(request: Request) -> Response:
            payload = await identity(request)
            csrf_check(await request.form(), payload)
            response = RedirectResponse(base + "/login", status_code=303)
            response.delete_cookie(cookie, path=base)
            return response

        @router.get("/")
        async def index(request: Request) -> Response:
            payload = await identity(request)
            if not payload:
                return RedirectResponse(base + "/login", status_code=303)
            cards = ""
            for key, admin in self._registry.items():
                if await admin.has_view_permission(request):
                    count = await (await admin.get_queryset(request)).count()
                    cards += (
                        f'<section class="card"><h2>{ui.e(label(admin))}</h2>'
                        f'<div class="metric">{count:,}</div><p class="muted">Total records</p>'
                        f'<a href="{base}/{key}/">Manage records →</a></section>'
                    )
            body = '<h1>Workspace overview</h1><p class="muted">Your data, organized and ready to manage.</p>'
            body += (
                f'<div class="grid">{cards}</div>'
                if cards
                else (
                    '<div class="card empty"><h2>No models available</h2>'
                    "<p>Register a ModelAdmin or ask an administrator for access.</p></div>"
                )
            )
            return await render(request, "Overview", body, payload)

        async def resolve(request: Request, key: str) -> tuple[dict, ModelAdmin | None]:
            payload = await identity(request)
            if not payload:
                return {}, None
            admin = self._registry.get(key)
            if admin is None:
                raise HTTPException(404)
            if not await admin.has_view_permission(request):
                raise HTTPException(403)
            return payload, admin

        @router.get("/{key}/")
        async def changelist(request: Request, key: str) -> Response:
            payload, admin = await resolve(request, key)
            if admin is None:
                return RedirectResponse(base + "/login", status_code=303)
            query = await admin.get_queryset(request)
            search = request.query_params.get("q", "")[:200]
            if search and admin.search_fields:
                query = query.filter(
                    Q(
                        *[Q(**{f"{f}__icontains": search}) for f in admin.search_fields],
                        join_type="OR",
                    )
                )
            filters = ""
            try:
                for name in admin.list_filter:
                    value = request.query_params.get(name, "")
                    if value:
                        field = admin.model._meta.fields_map[name]
                        query = query.filter(**{name: convert(field, value)})
                    filters += (
                        f"<label>{ui.e(name.replace('_', ' ').title())}"
                        f'<input name="{ui.e(name)}" value="{ui.e(value)}" '
                        'placeholder="Any value"></label>'
                    )
                number = max(1, int(request.query_params.get("page", "1")))
            except (ValueError, TypeError, ValidationError):
                return await render(
                    request,
                    "Invalid filter",
                    f'<h1>Invalid filter</h1><p><a href="{base}/{key}/">Reset filters</a></p>',
                    payload,
                    400,
                )
            columns = admin.list_display or (admin.model._meta.pk_attr,)
            sortable = set(admin.model._meta.fields_db_projection) & set(columns)
            order = request.query_params.get("o", "")
            ordering = (order,) if order.lstrip("-") in sortable else admin.ordering
            query = query.order_by(*(ordering or (admin.model._meta.pk_attr,)))
            count = await query.count()
            pages = max(1, (count + admin.list_per_page - 1) // admin.list_per_page)
            number = min(number, pages)
            objects = await query.offset((number - 1) * admin.list_per_page).limit(
                admin.list_per_page
            )
            root = f"{base}/{key}/"

            def url(**values: Any) -> str:
                return root + "?" + ui.e(urlencode({**request.query_params, **values}))

            headings = '<th scope="col"><input type="checkbox" data-select-all aria-label="Select all records"></th>'
            for name in columns:
                title = ui.e(name.replace("_", " ").title())
                if name in sortable:
                    sort = "-" + name if order == name else name
                    title = f'<a href="{url(o=sort, page=1)}">{title} ↕</a>'
                headings += f'<th scope="col">{title}</th>'
            rows = ""
            for obj in objects:
                if not await admin.has_view_permission(request, obj):
                    continue
                cells = f'<td><input type="checkbox" name="selected" value="{ui.e(obj.pk)}" aria-label="Select record {ui.e(obj.pk)}"></td>'
                for i, name in enumerate(columns):
                    value = (
                        "********"
                        if name in admin.password_fields
                        else await admin.get_list_value(request, obj, name)
                    )
                    value = ui.e(value if value is not None else "—")
                    if i == 0:
                        value = f'<a href="{root}{quote(str(obj.pk), safe="")}/change">{value}</a>'
                    cells += f"<td>{value}</td>"
                rows += f"<tr>{cells}</tr>"
            add = (
                f'<a class="button primary" href="{root}add">+ Add record</a>'
                if await admin.has_add_permission(request)
                else ""
            )
            body = (
                f'<div class="heading"><div><h1>{ui.e(label(admin))}</h1>'
                f'<p class="muted">{count:,} records</p></div>{add}</div>'
                f'<form class="card filters"><label>Search<input name="q" '
                f'value="{ui.e(search)}" placeholder="Search records"></label>{filters}'
                f'<button class="primary">Apply</button><a href="{root}">Reset</a></form>'
            )
            action_options = ""
            for action in admin.actions:
                if await admin.has_action_permission(request, action):
                    action_options += f'<option value="{ui.e(action)}">{ui.e(action.replace("_", " ").title())}</option>'
            body += f'<form method="post" action="{root}actions">{ui.token(payload["nonce"])}'
            if action_options:
                body += '<div class="actions"><label for="action">With selected</label>'
                body += f'<select id="action" name="action">{action_options}</select><button>Continue</button></div>'
            body += (
                f'<div class="card table-wrap"><table><thead><tr>{headings}</tr></thead>'
                f"<tbody>{rows}</tbody></table></div>"
                if rows
                else '<div class="card empty"><h2>No records found</h2><p>Try another search or add a record.</p></div>'
            )
            body += '</form><div class="pagination">'
            body += (
                f'<a href="{url(page=number - 1)}">← Previous</a>'
                if number > 1
                else "<span></span>"
            )
            body += f"<span>Page {number} of {pages}</span>"
            body += (
                f'<a href="{url(page=number + 1)}">Next →</a>'
                if number < pages
                else "<span></span>"
            )
            return await render(request, label(admin), body + "</div>", payload)

        @router.post("/{key}/actions")
        async def actions(request: Request, key: str) -> Response:
            payload, admin = await resolve(request, key)
            if admin is None:
                return RedirectResponse(base + "/login", status_code=303)
            form = await request.form()
            csrf_check(form, payload)
            action = str(form.get("action", ""))
            if action not in admin.actions or not await admin.has_action_permission(
                request, action
            ):
                raise HTTPException(403)
            selected = list(dict.fromkeys(str(v) for v in form.getlist("selected")))
            if not selected or len(selected) > 200:
                return await render(
                    request,
                    "Select records",
                    "<h1>Select between 1 and 200 records</h1>"
                    f'<a href="{base}/{key}/">Back to list</a>',
                    payload,
                    400,
                )
            try:
                query = (await admin.get_queryset(request)).filter(pk__in=selected)
                objects = await query
            except (ValueError, TypeError, ValidationError):
                raise HTTPException(400, "Invalid record selection") from None
            if len(objects) != len(selected):
                raise HTTPException(404)
            for obj in objects:
                if not await admin.has_view_permission(request, obj):
                    raise HTTPException(403)
                if action == "delete_selected" and not await admin.has_delete_permission(
                    request, obj
                ):
                    raise HTTPException(403)
                if action not in (
                    "delete_selected",
                    "export_csv",
                ) and not await admin.has_change_permission(request, obj):
                    raise HTTPException(403)
            if action == "export_csv":
                buffer = io.StringIO()
                writer = csv.writer(buffer)
                columns = admin.export_fields or admin.list_display or (admin.model._meta.pk_attr,)
                columns = tuple(name for name in columns if name not in admin.password_fields)
                writer.writerow(columns)
                for obj in objects:
                    row = []
                    for name in columns:
                        value = str(await admin.get_list_value(request, obj, name))
                        if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(
                            ("\t", "\r", "\n")
                        ):
                            value = "'" + value
                        row.append(value)
                    writer.writerow(row)
                return Response(
                    buffer.getvalue(),
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f'attachment; filename="{key}.csv"',
                        "Cache-Control": "no-store",
                    },
                )
            if form.get("confirmed") != "yes":
                items = "".join(f"<li>{ui.e(obj)}</li>" for obj in objects)
                hidden = "".join(
                    f'<input type="hidden" name="selected" value="{ui.e(pk)}">' for pk in selected
                )
                body = f'<h1>Confirm {ui.e(action.replace("_", " "))}</h1><div class="card"><ul>{items}</ul>'
                body += "<p>This operation may permanently change these records and their related data.</p>"
                body += f'<form method="post">{ui.token(payload["nonce"])}{hidden}'
                body += f'<input type="hidden" name="action" value="{ui.e(action)}">'
                body += '<input type="hidden" name="confirmed" value="yes"><div class="actions">'
                body += f'<button class="danger">Confirm action</button><a href="{base}/{key}/">Cancel</a></div></form></div>'
                return await render(request, "Confirm action", body, payload)
            async with in_transaction(admin.model._meta.default_connection):
                for obj in objects:
                    if action == "delete_selected":
                        await admin.delete_model(request, obj)
                    else:
                        # Custom async methods receive one permission-checked object at a time.
                        await invoke(getattr(admin, action), request, obj)
                    await audit(request, key, obj, action)
            return RedirectResponse(f"{base}/{key}/?saved=1", status_code=303)

        @router.get("/{key}/{pk}/history")
        async def history(request: Request, key: str, pk: str) -> Response:
            payload, admin = await resolve(request, key)
            if admin is None:
                return RedirectResponse(base + "/login", status_code=303)
            try:
                obj = await (await admin.get_queryset(request)).filter(pk=pk).first()
            except (ValueError, TypeError, ValidationError):
                raise HTTPException(404) from None
            if obj is None or not await admin.has_view_permission(request, obj):
                raise HTTPException(404)
            entries = await AdminLogEntry.filter(site=base, model=key, object_id=pk).limit(100)
            rows = "".join(
                f"<tr><td>{ui.e(entry.created_at)}</td><td>{ui.e(entry.actor)}</td>"
                f"<td>{ui.e(entry.action)}</td><td>{ui.e(', '.join(entry.changed_fields))}</td></tr>"
                for entry in entries
            )
            body = f'<a href="{base}/{key}/{quote(pk, safe="")}/change">← Back to record</a><h1>Change history</h1>'
            body += (
                '<p class="muted">Latest 100 admin operations. Field values are never logged.</p>'
            )
            body += (
                f'<div class="card table-wrap"><table><thead><tr><th>When</th><th>Who</th><th>Action</th><th>Fields</th></tr></thead><tbody>{rows}</tbody></table></div>'
                if rows
                else '<div class="card empty">No changes recorded yet.</div>'
            )
            return await render(request, "Change history", body, payload)

        @router.api_route("/{key}/add", methods=["GET", "POST"])
        @router.api_route("/{key}/{pk}/change", methods=["GET", "POST"])
        @router.api_route("/{key}/{pk}/delete", methods=["GET", "POST"])
        async def change(request: Request, key: str, pk: str | None = None) -> Response:
            payload, admin = await resolve(request, key)
            if admin is None:
                return RedirectResponse(base + "/login", status_code=303)
            obj = None
            if pk is not None:
                try:
                    obj = await (await admin.get_queryset(request)).filter(pk=pk).first()
                except (ValueError, TypeError, ValidationError):
                    raise HTTPException(404) from None
                if obj is None:
                    raise HTTPException(404)
                if not await admin.has_view_permission(request, obj):
                    raise HTTPException(403)
            delete = request.url.path.endswith("/delete")
            allowed = (
                await admin.has_delete_permission(request, obj)
                if delete
                else await admin.has_change_permission(request, obj)
                if obj is not None
                else await admin.has_add_permission(request)
            )
            if (delete and not allowed) or (request.method == "POST" and not allowed):
                raise HTTPException(403)
            if obj is None and not allowed:
                raise HTTPException(403)
            title = (
                ("Delete" if delete else "Edit" if obj is not None else "Add") + " " + label(admin)
            )
            root = f"{base}/{key}/"
            error = ""
            status = 200
            form: Any = {}
            if request.method == "POST":
                form = await request.form()
                csrf_check(form, payload)
                try:
                    if delete:
                        assert obj is not None
                        async with in_transaction(admin.model._meta.default_connection):
                            await admin.delete_model(request, obj)
                            await audit(request, key, obj, "delete")
                    else:
                        values = {}
                        relations = {}
                        for name in admin.get_fields(obj is not None):
                            if name in admin.readonly_fields:
                                continue
                            field = admin.model._meta.fields_map[name]
                            if name in admin.model._meta.m2m_fields:
                                ids = [str(v) for v in form.getlist(name) if str(v)]
                                if len(ids) == 1 and "," in ids[0]:
                                    ids = [v.strip() for v in ids[0].split(",") if v.strip()]
                                if len(ids) > 200:
                                    raise ValueError("Too many related records")
                                choices = await admin.get_field_choices(request, name)
                                if choices is not None and not set(ids) <= {
                                    str(v) for v, _ in choices
                                }:
                                    raise ValueError("Invalid related record")
                                related_model = getattr(field, "related_model", None)
                                if related_model is None:
                                    raise ValueError("Unknown related model")
                                related = await related_model.filter(pk__in=ids)
                                if len(related) != len(set(ids)):
                                    raise ValueError("Unknown related record")
                                relations[name] = related
                                continue
                            raw = str(form.get(name, ""))
                            choices = await admin.get_field_choices(request, name)
                            if (
                                raw
                                and choices is not None
                                and raw not in {str(v) for v, _ in choices}
                            ):
                                raise ValueError("Invalid choice")
                            if obj is None and raw == "" and field.default is not None:
                                continue
                            value = convert(field, raw)
                            field.validate(value)
                            values[name] = value
                        values = await admin.clean(request, values, obj)
                        if obj is None:
                            obj = admin.model(**values)
                        else:
                            obj.update_from_dict(values)
                        async with in_transaction(admin.model._meta.default_connection):
                            await admin.save_model(request, obj, pk is not None)
                            for name, related in relations.items():
                                manager = getattr(obj, name)
                                await manager.clear()
                                if related:
                                    await manager.add(*related)
                            await audit(
                                request,
                                key,
                                obj,
                                "change" if pk is not None else "add",
                                [*values, *relations],
                            )
                    destination = root + "?saved=1"
                    if form.get("_continue") and not delete:
                        assert obj is not None
                        destination = root + quote(str(obj.pk), safe="") + "/change?saved=1"
                    elif form.get("_addanother") and not delete:
                        destination = root + "add?saved=1"
                    return RedirectResponse(destination, status_code=303)
                except (ValueError, TypeError, ValidationError, IntegrityError):
                    error = '<p class="error" role="alert">Unable to save. Check required fields, formats, unique values and related records.</p>'
                    status = 400
            body = f'<a href="{root}">← {ui.e(label(admin))}</a><h1>{ui.e(title)}</h1>{error}'
            if delete:
                body += (
                    f'<div class="card"><h2>Delete this record?</h2><p>Record: {ui.e(obj)}</p>'
                    "<p>This cannot be undone. Related records may also be deleted according "
                    "to the model database relationship rules.</p>"
                    f'<form method="post">{ui.token(payload["nonce"])}<div class="actions">'
                    f'<button class="danger">Confirm deletion</button><a href="{root}">Cancel</a>'
                    "</div></form></div>"
                )
            else:
                body += f'<form method="post" class="card">{ui.token(payload["nonce"])}<h2>Record details</h2>'
                for name in admin.get_fields(pk is not None):
                    field = admin.model._meta.fields_map[name]
                    value = (
                        form.get(name, "")
                        if request.method == "POST"
                        else (
                            getattr(obj, name, "")
                            if obj is not None
                            else (field.default if not callable(field.default) else "")
                        )
                    )
                    multiple = name in admin.model._meta.m2m_fields
                    if multiple:
                        value = (
                            form.getlist(name)
                            if request.method == "POST"
                            else (
                                [str(item.pk) for item in await getattr(obj, name).all()]
                                if obj is not None
                                else []
                            )
                        )
                    readonly = not allowed or name in admin.readonly_fields
                    for section, options in admin.fieldsets:
                        if options["fields"] and name == options["fields"][0]:
                            body += f"<h2>{ui.e(section)}</h2>"
                            if options.get("description"):
                                body += f'<p class="muted">{ui.e(options["description"])}</p>'
                    body += widget(
                        name,
                        field,
                        value,
                        readonly,
                        choices=await admin.get_field_choices(request, name),
                        label=admin.labels.get(name),
                        help_text=admin.help_texts.get(name),
                        multiple=multiple,
                        password=name in admin.password_fields,
                    )
                body += '<div class="actions">'
                if allowed:
                    body += '<button class="primary">Save record</button>'
                    body += '<button name="_continue" value="1">Save and continue</button>'
                    if await admin.has_add_permission(request):
                        body += '<button name="_addanother" value="1">Save and add another</button>'
                body += f'<a class="button" href="{root}">Back to list</a>'
                if pk is not None:
                    body += f'<a href="{root}{quote(pk, safe="")}/history">History</a>'
                if pk is not None and await admin.has_delete_permission(request, obj):
                    body += f'<a href="{root}{quote(pk, safe="")}/delete">Delete record</a>'
                body += "</div></form>"
            return await render(request, title, body, payload, status)

        app.include_router(router)


def label(admin: ModelAdmin) -> str:
    return admin.verbose_name or admin.model.__name__


def convert(field: Any, raw: str) -> Any:
    if raw == "" and field.null:
        return None
    if isinstance(field, fields.BooleanField):
        if raw not in ("true", "false", "on", "", "1", "0"):
            raise ValueError("Invalid boolean")
        return raw in ("true", "on", "1")
    if isinstance(field, fields.JSONField):
        return json.loads(raw)
    if raw == "" and not isinstance(field, fields.CharField | fields.TextField):
        raise ValueError("Required field")
    return field.to_python_value(raw)


def widget(
    name: str,
    field: Any,
    value: Any,
    readonly: bool,
    *,
    choices: list | None = None,
    label: str | None = None,
    help_text: str | None = None,
    multiple: bool = False,
    password: bool = False,
) -> str:
    title = ui.e(label or name.replace("_", " ").title())
    if password:
        return (
            f'<div class="field"><label for="{ui.e(name)}">{title}</label>'
            f'<input id="{ui.e(name)}" name="{ui.e(name)}" type="password" autocomplete="new-password"'
            f"{' disabled' if readonly else ''}><small>{ui.e(help_text or 'Password')}</small></div>"
        )
    if readonly:
        return f'<div class="field"><label>{title}</label><p>{ui.e(value)}</p><small>Read only</small></div>'
    if isinstance(value, dict | list) and not multiple:
        value = json.dumps(value, indent=2)
    if value is None:
        value = ""
    required = " required" if not multiple and not field.null and field.default is None else ""
    attrs = f'id="{ui.e(name)}" name="{ui.e(name)}"{required}'
    if multiple:
        selected = {str(v) for v in value}
        if choices is not None:
            control = f'<select {attrs} multiple size="6">'
            control += "".join(
                f'<option value="{ui.e(v)}"{" selected" if str(v) in selected else ""}>{ui.e(t)}</option>'
                for v, t in choices
            )
            control += "</select>"
            help_text = help_text or "Choose multiple related records (Ctrl or Command + click)."
        else:
            control = f'<input {attrs} value="{ui.e(", ".join(sorted(selected)))}">'
            help_text = help_text or "Related record IDs, separated by commas (maximum 200)."
    elif isinstance(field, fields.BooleanField):
        choices = [("true", "Yes"), ("false", "No")]
        if field.null:
            choices.insert(0, ("", "Unknown"))
        current = (
            "true"
            if value in (True, "true", "on")
            else "false"
            if value in (False, "false")
            else ""
        )
        control = (
            f"<select {attrs}>"
            + "".join(
                f'<option value="{v}"{" selected" if v == current else ""}>{t}</option>'
                for v, t in choices
            )
            + "</select>"
        )
    elif choices is not None:
        control = f'<select {attrs}><option value="">— Select —</option>'
        control += "".join(
            f'<option value="{ui.e(v)}"{" selected" if str(v) == str(value) else ""}>{ui.e(t)}</option>'
            for v, t in choices
        )
        control += "</select>"
    elif isinstance(field, fields.TextField | fields.JSONField):
        control = f"<textarea {attrs}>{ui.e(value)}</textarea>"
    else:
        kind = "text"
        if isinstance(field, fields.IntField | fields.FloatField | fields.DecimalField):
            kind = "number"
        elif isinstance(field, fields.DatetimeField):
            kind = "datetime-local"
        elif isinstance(field, fields.DateField):
            kind = "date"
        if isinstance(value, datetime):
            if value.tzinfo is not None:
                value = value.astimezone(UTC).replace(tzinfo=None)
            value = value.isoformat()
            help_text = help_text or "Date and time in UTC."
        elif isinstance(value, date):
            value = value.isoformat()
        control = f'<input {attrs} type="{kind}" step="any" value="{ui.e(value)}">'
    help_text = help_text or (
        "JSON value"
        if isinstance(field, fields.JSONField)
        else (
            "Optional"
            if field.null
            else "Required"
            if required
            else "Uses model default when omitted on creation"
        )
    )
    return f'<div class="field"><label for="{ui.e(name)}">{title}</label>{control}<small>{ui.e(help_text)}</small></div>'
