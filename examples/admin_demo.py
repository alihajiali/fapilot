"""Local admin showcase: ADMIN_DEMO_PASSWORD='...' uvicorn examples.admin_demo:app."""

import os
import secrets
from typing import ClassVar

from tortoise import fields
from tortoise.models import Model

from fapilot import create_app
from fapilot.admin import ModelAdmin, create_staff_site, register
from fapilot.admin.auth import make_password
from fapilot.admin.models import StaffUser
from fapilot.conf import FapilotSettings


class Category(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=120)
    category = fields.ForeignKeyField("catalog.Category", related_name="products")
    price = fields.DecimalField(max_digits=10, decimal_places=2)
    stock = fields.IntField(default=0)
    active = fields.BooleanField(default=True)
    description = fields.TextField(default="")
    created_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.name


site = create_staff_site(title="Fapilot Studio")


@register(Product, site=site, name="products")
class ProductAdmin(ModelAdmin):
    verbose_name = "Products"
    list_display = ("id", "name", "price", "stock", "active")
    search_fields = ("name", "description")
    list_filter = ("active",)
    ordering = ("name",)
    fieldsets = (
        ("Product information", {"fields": ("name", "category_id", "description")}),
        ("Inventory", {"fields": ("price", "stock", "active")}),
    )
    labels: ClassVar[dict[str, str]] = {"category_id": "Category"}
    help_texts: ClassVar[dict[str, str]] = {
        "stock": "Units available for sale.",
        "price": "Price in USD.",
    }
    actions = ("export_csv", "archive", "delete_selected")

    async def archive(self, request, obj):
        obj.active = False
        await obj.save(update_fields=["active"])


@register(Category, site=site, name="categories")
class CategoryAdmin(ModelAdmin):
    verbose_name = "Categories"
    list_display = ("id", "name")
    search_fields = ("name",)


app = create_app(
    FapilotSettings(
        DEBUG=True,
        SECRET_KEY=secrets.token_urlsafe(48),
        ADMIN_ENABLED=True,
        ADMIN_SITE="examples.admin_demo.site",
        ADMIN_SECURE_COOKIES=False,
        DATABASE_URL="sqlite://:memory:",
        DATABASES={},
        DATABASE_APPS={"catalog": {"models": ["examples.admin_demo"]}},
        INSTALLED_APPS=[],
        MIDDLEWARE=[],
    )
)


async def seed(app):
    password = os.environ.get("ADMIN_DEMO_PASSWORD", "")
    if len(password) < 12:
        raise ValueError("Set ADMIN_DEMO_PASSWORD to a password of at least 12 characters")
    await StaffUser.create(username="admin", password=make_password(password), is_superuser=True)
    category = await Category.create(name="Workspace essentials")
    for name, price, stock in (
        ("Studio headphones", "149.00", 42),
        ("Desk lamp", "68.00", 18),
        ("Everyday notebook", "24.00", 120),
        ("Mechanical keyboard", "189.00", 27),
        ("Canvas tote", "32.00", 64),
        ("Ceramic mug", "28.00", 36),
    ):
        await Product.create(
            name=name,
            price=price,
            stock=stock,
            category=category,
            description="Thoughtfully made for your everyday workspace.",
        )


app.state.fapilot.events.connect("startup", seed)
