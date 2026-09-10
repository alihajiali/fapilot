"""Interactive staff bootstrapping without default or command-line passwords."""

import asyncio
from getpass import getpass

from fapilot.admin.auth import make_password
from fapilot.admin.models import StaffUser
from fapilot.apps import AppRegistry
from fapilot.conf import get_settings
from fapilot.db.tortoise import close_orm, init_orm


def createsuperuser() -> None:
    settings = get_settings()
    if not settings.ADMIN_ENABLED:
        raise ValueError("Set ADMIN_ENABLED=True and migrate the models group first")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass("Password (12+ characters): ")
    if password != getpass("Confirm password: "):
        raise ValueError("Passwords do not match")
    if not username or len(username) > 150 or len(email) > 254:
        raise ValueError("Provide a username up to 150 characters and an email up to 254")
    encoded = make_password(password)

    async def create() -> None:
        registry = AppRegistry()
        registry.populate(settings.INSTALLED_APPS)
        try:
            await init_orm(settings, registry)
            await StaffUser.create(
                username=username,
                email=email,
                password=encoded,
                is_superuser=True,
                is_staff=True,
                is_active=True,
            )
        finally:
            await close_orm()

    asyncio.run(create())
    print(f"Created administrator {username!r}.")
