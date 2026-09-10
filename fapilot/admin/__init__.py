"""Django-style registration with an independent, themed admin interface."""

from fapilot.admin.auth import create_staff_site
from fapilot.admin.options import ModelAdmin
from fapilot.admin.site import AdminSite

site = create_staff_site()


def register(model, *, site=site, name=None):
    """Register a ModelAdmin subclass using a decorator."""

    def decorator(admin_class):
        site.register(model, admin_class, name=name)
        return admin_class

    return decorator


__all__ = ["AdminSite", "ModelAdmin", "create_staff_site", "register", "site"]
