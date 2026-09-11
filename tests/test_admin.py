import re
import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tortoise import fields
from tortoise.models import Model

from fapilot import create_app
from fapilot.admin import AdminSite, ModelAdmin, register
from fapilot.architectures import ARCHITECTURES
from fapilot.cli import start_app, start_project
from fapilot.conf import FapilotSettings


class Article(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=100, unique=True)
    published = fields.BooleanField(default=False)
    metadata = fields.JSONField(default=dict)
    secret = fields.CharField(max_length=100, default="private")

    def __str__(self):
        return self.title


class ArticleAdmin(ModelAdmin):
    list_display = ("id", "title", "published")
    search_fields = ("title",)
    list_filter = ("published",)
    exclude = ("secret",)
    list_per_page = 2
    fieldsets = (("Content", {"fields": ("title", "published", "metadata")}),)
    actions = ("delete_selected", "export_csv", "publish")

    async def publish(self, request, obj):
        obj.published = True
        await obj.save()

    async def has_change_permission(self, request, obj=None):
        return obj is None or obj.title != "Locked"

    async def has_delete_permission(self, request, obj=None):
        return obj is None or obj.title != "Locked"


@pytest.fixture
def admin_client(tmp_path, monkeypatch):
    state = {"active": True}
    site = AdminSite(
        authenticate=lambda request, username, password: "staff"
        if (username == "staff" and password == "correct")
        else None,
        authorize=lambda request, user: state["active"] and user == "staff",
    )
    site.register(Article, ArticleAdmin, name="articles")
    module = types.ModuleType("admin_test_config")
    module.__dict__.update(site=site, __models__=[Article])
    monkeypatch.setitem(sys.modules, module.__name__, module)
    app = create_app(
        FapilotSettings(
            DEBUG=True,
            SECRET_KEY="a" * 40,
            ADMIN_ENABLED=True,
            ADMIN_SITE="admin_test_config.site",
            ADMIN_SECURE_COOKIES=False,
            INSTALLED_APPS=[],
            MIDDLEWARE=[],
            DATABASES={},
            DATABASE_URL=f"sqlite://{tmp_path / 'admin.sqlite3'}",
            DATABASE_APPS={"articles": {"models": ["admin_test_config"]}},
        )
    )
    with TestClient(app) as client:
        yield client, state, site


def csrf(response):
    return re.search(r'name="_csrf" value="([^"]+)"', response.text).group(1)


def login(client):
    token = csrf(client.get("/admin/login"))
    response = client.post(
        "/admin/login",
        data={
            "_csrf": token,
            "username": "staff",
            "password": "correct",
        },
    )
    assert response.status_code == 200
    assert "Workspace overview" in response.text
    return csrf(response)


def add(client, title, **values):
    token = csrf(client.get("/admin/articles/add"))
    return client.post(
        "/admin/articles/add",
        data={
            "_csrf": token,
            "title": title,
            "published": "false",
            "metadata": "{}",
            **values,
        },
    )


def test_authentication_csrf_and_revocation(admin_client):
    client, state, _ = admin_client
    assert client.get("/admin/").url.path == "/admin/login"
    assert client.post("/admin/login", data={"username": "staff"}).status_code == 403
    token = login(client)
    assert client.post("/admin/articles/add", data={"title": "Bad"}).status_code == 403
    assert client.post("/admin/articles/add", data={"_csrf": "forged"}).status_code == 403
    state["active"] = False
    assert client.get("/admin/articles/").url.path == "/admin/login"
    state["active"] = True
    assert client.post("/admin/logout", data={"_csrf": token}).url.path == "/admin/login"
    assert client.get("/admin/").url.path == "/admin/login"


def test_crud_filters_history_validation_and_themes(admin_client):
    client, _, _ = admin_client
    login(client)
    assert add(client, "First").status_code == 200
    assert add(client, "First").status_code == 400
    assert add(client, "Invalid", metadata="not json").status_code == 400
    assert add(client, "Second", published="true").status_code == 200
    assert add(client, "Third").status_code == 200
    listing = client.get("/admin/articles/")
    assert "Page 1 of 2" in listing.text
    assert "Third" not in listing.text
    assert "Third" in client.get("/admin/articles/?page=2").text
    assert "First" not in client.get("/admin/articles/?published=true").text
    assert "Second" in client.get("/admin/articles/?q=Second").text
    assert client.get("/admin/articles/?page=bad").status_code == 400
    assert client.get("/admin/articles/?published=bad").status_code == 400
    edit = client.get("/admin/articles/1/change")
    assert 'value="false" selected' in client.get("/admin/articles/add").text
    assert "secret" not in edit.text
    token = csrf(edit)
    response = client.post(
        "/admin/articles/1/change",
        data={
            "_csrf": token,
            "title": "Changed",
            "published": "true",
            "metadata": '{"ok": true}',
            "secret": "injected",
            "_continue": "1",
        },
    )
    assert response.status_code == 200
    assert response.url.path.endswith("/1/change")
    history = client.get("/admin/articles/1/history")
    assert "staff" in history.text and "change" in history.text
    assert "private" not in history.text
    assert client.get("/admin/articles/999/change").status_code == 404
    assert client.get("/admin/articles/not-an-id/change").status_code == 404
    assert "data-theme=dark" in client.get("/admin/assets/admin.css").text
    assert "localStorage" in client.get("/admin/assets/admin.js").text
    assert "frame-ancestors 'none'" in edit.headers["content-security-policy"]
    confirm = client.get("/admin/articles/1/delete")
    assert "cannot be undone" in confirm.text
    assert client.post("/admin/articles/1/delete", data={"_csrf": csrf(confirm)}).status_code == 200
    assert client.get("/admin/articles/1/change").status_code == 404


def test_bulk_actions_permissions_export_and_escaping(admin_client):
    client, _, _ = admin_client
    login(client)
    add(client, "=FORMULA()")
    add(client, "Locked")
    add(client, '<script>alert("x")</script>')
    token = csrf(client.get("/admin/"))
    assert "&lt;script&gt;" in client.get("/admin/articles/?page=2").text
    export = client.post(
        "/admin/articles/actions",
        data={
            "_csrf": token,
            "action": "export_csv",
            "selected": "1",
        },
    )
    assert export.status_code == 200
    assert "'=FORMULA()" in export.text
    assert "private" not in export.text
    assert client.post("/admin/articles/2/change", data={"_csrf": token}).status_code == 403
    assert client.get("/admin/articles/2/delete").status_code == 403
    assert (
        client.post(
            "/admin/articles/actions",
            data={
                "_csrf": token,
                "action": "delete_selected",
                "selected": ["1", "2"],
                "confirmed": "yes",
            },
        ).status_code
        == 403
    )
    assert client.get("/admin/articles/1/change").status_code == 200
    confirmation = client.post(
        "/admin/articles/actions",
        data={
            "_csrf": token,
            "action": "publish",
            "selected": ["1", "3"],
        },
    )
    assert "Confirm publish" in confirmation.text
    assert "=FORMULA()" not in client.get("/admin/articles/?published=true").text
    assert (
        client.post(
            "/admin/articles/actions",
            data={
                "_csrf": token,
                "action": "publish",
                "selected": ["1", "3"],
                "confirmed": "yes",
            },
        ).status_code
        == 200
    )
    assert "=FORMULA()" in client.get("/admin/articles/?published=true").text
    assert (
        client.post(
            "/admin/articles/actions",
            data={
                "_csrf": token,
                "action": "delete_selected",
                "selected": ["1", "3"],
                "confirmed": "yes",
            },
        ).status_code
        == 200
    )
    assert client.get("/admin/articles/1/change").status_code == 404


def test_registry_and_secret_configuration():
    site = AdminSite()
    register(Article, site=site, name="article")(ArticleAdmin)
    with pytest.raises(ValueError, match="already registered"):
        site.register(Article)
    site.unregister(Article)
    with pytest.raises(KeyError):
        site.unregister(Article)
    with pytest.raises(ValueError, match="SECRET_KEY"):
        site.mount(FastAPI(), secret_key="change-me")


@pytest.mark.parametrize("architecture", [None, *ARCHITECTURES])
def test_all_architectures_include_admin_configuration(tmp_path, monkeypatch, architecture):
    monkeypatch.chdir(tmp_path)
    start_project("demo", architecture=architecture)
    assert "create_staff_site" in (tmp_path / "demo/config/admin.py").read_text()
    assert 'ADMIN_SITE = "config.admin.site"' in (tmp_path / "demo/config/settings.py").read_text()
    monkeypatch.chdir(tmp_path / "demo")
    start_app("records")
    assert "ModelAdmin" in (tmp_path / "demo/apps/records/admin.py").read_text()


@pytest.fixture
def staff_client(tmp_path, monkeypatch):
    from fapilot.admin import create_staff_site
    from fapilot.admin.auth import make_password
    from fapilot.admin.models import StaffUser

    site = create_staff_site()
    site.register(Article, ModelAdmin, name="articles")
    module = types.ModuleType("staff_test_config")
    module.__dict__.update(site=site, __models__=[Article])
    monkeypatch.setitem(sys.modules, module.__name__, module)
    app = create_app(
        FapilotSettings(
            DEBUG=True,
            SECRET_KEY="s" * 40,
            ADMIN_ENABLED=True,
            ADMIN_SITE="staff_test_config.site",
            ADMIN_SECURE_COOKIES=False,
            INSTALLED_APPS=[],
            MIDDLEWARE=[],
            DATABASES={},
            DATABASE_URL=f"sqlite://{tmp_path / 'staff.sqlite3'}",
            DATABASE_APPS={"articles": {"models": ["staff_test_config"]}},
        )
    )

    async def seed(app):
        await StaffUser.create(
            username="root", password=make_password("a secure password"), is_superuser=True
        )

    app.state.fapilot.events.connect("startup", seed)
    with TestClient(app) as client:
        yield client


def staff_login(client, username="root", password="a secure password"):
    response = client.post(
        "/admin/login",
        data={
            "_csrf": csrf(client.get("/admin/login")),
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 200
    return csrf(response)


def test_staff_users_groups_passwords_and_permissions(staff_client):
    client = staff_client
    token = staff_login(client)
    assert "Staff users" in client.get("/admin/").text
    group = client.post(
        "/admin/staff-groups/add",
        data={
            "_csrf": token,
            "name": "Readers",
            "permissions": '["articles.view"]',
        },
    )
    assert group.status_code == 200
    user = client.post(
        "/admin/staff-users/add",
        data={
            "_csrf": token,
            "username": "reader",
            "email": "reader@example.test",
            "password": "another strong password",
            "is_active": "true",
            "is_staff": "true",
            "is_superuser": "false",
            "groups": "1",
        },
    )
    assert user.status_code == 200
    edit = client.get("/admin/staff-users/2/change")
    assert 'value="1" selected' in edit.text
    assert "pbkdf2_sha256" not in edit.text
    assert "another strong password" not in edit.text
    assert client.get("/admin/staff-users/1/delete").status_code == 403
    client.post("/admin/logout", data={"_csrf": token})
    token = staff_login(client, "reader", "another strong password")
    assert client.get("/admin/articles/").status_code == 200
    assert client.get("/admin/articles/add").status_code == 403
    assert client.get("/admin/staff-users/").status_code == 403
    assert client.get("/admin/staff-groups/").status_code == 403
    saved_cookie = client.cookies.get("fapilot_admin_admin")
    changed = client.post(
        "/admin/password",
        data={
            "_csrf": token,
            "old_password": "another strong password",
            "new_password": "a different password",
            "confirm_password": "a different password",
        },
    )
    assert changed.url.path == "/admin/login"
    client.cookies.set(
        "fapilot_admin_admin", saved_cookie, domain="testserver.local", path="/admin"
    )
    assert client.get("/admin/articles/").url.path == "/admin/login"
    client.cookies.clear()
    staff_login(client, "reader", "a different password")


def test_failed_action_rolls_back_records_and_audit(admin_client):
    client, _, site = admin_client
    login(client)
    add(client, "One")
    add(client, "Two")
    admin = site._registry["articles"]

    async def failing_action(request, obj):
        obj.title = f"Mutated {obj.pk}"
        await obj.save()
        if obj.pk == 2:
            raise RuntimeError("Abort action")

    admin.fail = failing_action
    admin.actions = ("fail",)
    with pytest.raises(RuntimeError, match="Abort action"):
        client.post(
            "/admin/articles/actions",
            data={
                "_csrf": csrf(client.get("/admin/")),
                "action": "fail",
                "selected": ["1", "2"],
                "confirmed": "yes",
            },
        )
    assert "One" in client.get("/admin/articles/").text
    assert "Two" in client.get("/admin/articles/").text
    assert ">fail<" not in client.get("/admin/articles/1/history").text


def test_missing_auth_and_throttling(admin_client):
    client, _, site = admin_client
    site.authenticate = None
    for _ in range(10):
        response = client.post(
            "/admin/login",
            data={
                "_csrf": csrf(client.get("/admin/login")),
                "username": "bad",
                "password": "bad",
            },
        )
        assert response.status_code == 401
    response = client.post(
        "/admin/login",
        data={
            "_csrf": csrf(client.get("/admin/login")),
            "username": "bad",
            "password": "bad",
        },
    )
    assert response.status_code == 429


def test_autodiscovery_surfaces_broken_dependencies(tmp_path, monkeypatch):
    package = tmp_path / "brokenapp"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "admin.py").write_text("import dependency_that_does_not_exist\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(ModuleNotFoundError, match="dependency_that_does_not_exist"):
        AdminSite().autodiscover(["brokenapp"])


def test_overview_metrics_shortcuts_icons_and_scoped_activity(admin_client):
    client, _, site = admin_client
    login(client)
    add(client, "Visible")
    add(client, "Hidden")
    admin = site._registry["articles"]

    async def scoped(request):
        return Article.exclude(title="Hidden")

    admin.get_queryset = scoped
    admin.icon = "file-text"
    admin.description = "<script>private</script>"
    page = client.get("/admin/")
    assert page.status_code == 200
    assert "Managed records" in page.text
    assert "Available models" in page.text
    assert "Record distribution" in page.text
    assert "Your recent activity" in page.text
    assert "Record #1" in page.text
    assert "Record #2" not in page.text
    assert "&lt;script&gt;private&lt;/script&gt;" in page.text
    assert "<script>private</script>" not in page.text
    assert 'href="/admin/articles/add"' in page.text
    assert 'data-pin="articles"' in page.text
    assert 'aria-current="page"' in page.text
    assert '<svg class="icon" aria-hidden="true"' in page.text


def test_overview_hides_unavailable_models_and_quick_add(admin_client):
    client, _, site = admin_client
    login(client)
    add(client, "Visible")
    admin = site._registry["articles"]

    async def deny(*args):
        return False

    admin.has_add_permission = deny
    page = client.get("/admin/")
    assert 'href="/admin/articles/add"' not in page.text
    admin.has_view_permission = deny
    page = client.get("/admin/")
    assert "No models available" in page.text
    assert "Record #1" not in page.text
    assert 'data-model="articles"' not in page.text


def test_overview_activity_is_personal_and_icons_are_allowlisted(admin_client):
    from fapilot.admin.icons import icon

    client, _, site = admin_client
    login(client)
    add(client, "Created by staff")
    assert "Record #1" in client.get("/admin/").text
    client.cookies.clear()
    site.authenticate = lambda request, username, password: "other"
    site.authorize = lambda request, identifier: True
    token = csrf(client.get("/admin/login"))
    page = client.post(
        "/admin/login",
        data={
            "_csrf": token,
            "username": "other",
            "password": "password",
        },
    )
    assert "Record #1" not in page.text
    assert "A fresh start" in page.text
    assert icon("<script>") == icon("box")
