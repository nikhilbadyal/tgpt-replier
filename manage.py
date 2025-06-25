#!/usr/bin/env python
from pathlib import Path

import django
from django.conf import settings


def init_django() -> None:
    """Initialize Django.

    This function configures the Django settings to use an SQLite3
    database and the `sqlitedb` app. If the settings have already been
    configured, this function does nothing.
    """
    import environ  # noqa: PLC0415

    env = environ.Env()
    base_dir = Path(__file__).resolve().parent
    environ.Env.read_env(Path(base_dir, ".env"))

    if settings.configured:
        return
    settings.configure(
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        INSTALLED_APPS=[
            "sqlitedb",
        ],
        DATABASES={"default": env.db("DATABASE_URL")},
    )
    django.setup()


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    init_django()
    execute_from_command_line()
