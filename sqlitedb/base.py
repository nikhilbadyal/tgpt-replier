"""Custom Database Backend."""
import time

from django.db.backends.postgresql import base as postgresql_base
from django.db.utils import OperationalError


class DatabaseWrapper(postgresql_base.DatabaseWrapper):
    def ensure_connection(self):
        max_retries = 5
        delay = 1  # Time delay in seconds between retries

        for attempt in range(1, max_retries + 1):
            try:
                super().ensure_connection()
                break
            except OperationalError as e:
                print("Closing and retrying.")
                if 'SSL connection has been closed unexpectedly' in str(e):
                    self.close()
                    if attempt == max_retries:
                        raise e
                    time.sleep(delay)
                else:
                    raise e
