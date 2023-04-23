"""Custom Database Backend."""
from django.db.backends.postgresql import base as postgresql_base
from django.db.utils import OperationalError


class DatabaseWrapper(postgresql_base.DatabaseWrapper):
    def _cursor(self, name: str = None):
        try:
            return super()._cursor(name)
        except OperationalError as e:
            if "Connection already closed" in str(e):
                self.close()
                self.connect()
                return super()._cursor(name)
            else:
                raise e
