"""Persistent admin audit metadata (values and credentials are never recorded)."""

from tortoise import fields
from tortoise.models import Model


class AdminLogEntry(Model):
    id = fields.IntField(primary_key=True)
    site = fields.CharField(max_length=255, db_index=True)
    model = fields.CharField(max_length=255, db_index=True)
    object_id = fields.CharField(max_length=255, db_index=True)
    actor = fields.CharField(max_length=255)
    action = fields.CharField(max_length=100)
    changed_fields = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta(Model.Meta):
        table = "fapilot_admin_log"
        ordering = ("-created_at", "-id")


class StaffGroup(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=150, unique=True)
    permissions = fields.JSONField(default=list)

    def __str__(self) -> str:
        return self.name

    class Meta(Model.Meta):
        table = "fapilot_admin_group"


class StaffUser(Model):
    id = fields.IntField(primary_key=True)
    username = fields.CharField(max_length=150, unique=True)
    password = fields.CharField(max_length=255)
    email = fields.CharField(max_length=254, default="")
    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=True)
    is_superuser = fields.BooleanField(default=False)
    groups = fields.ManyToManyField("models.StaffGroup", related_name="users")
    joined_at = fields.DatetimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.username

    class Meta(Model.Meta):
        table = "fapilot_admin_user"
