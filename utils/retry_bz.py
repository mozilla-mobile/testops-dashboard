import random
import time
from bugzilla.exceptions import BugzillaHTTPError


def with_retry(func, *args, retries=5, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except BugzillaHTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                wait = int(e.response.headers.get("Retry-After", 2 ** attempt))
                wait += random.uniform(0, 1)  # jitter
                print(f"429 received, sleeping {wait:.2f}s before retry...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Max retries exceeded")
