#!/usr/bin/env python
from pathlib import Path


def init_django() -> None:
    """Initialize Django.

    This function configures the Django settings to use an SQLite3
    database and the `sqlitedb` app. If the settings have already been
    configured, this function does nothing.
    """

    import django
    from django.conf import settings

    BASE_DIR = Path(__file__).resolve().parent

    if settings.configured:
        return
    settings.configure(
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        INSTALLED_APPS=[
            "sqlitedb",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / f"{Path(__file__).resolve().parent.name}.db",
            }
        },
    )
    django.setup()


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    init_django()
    execute_from_command_line()
