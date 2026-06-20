"""Small time helper.

`datetime.utcnow()` is deprecated as of Python 3.12. `utcnow()` here is a
drop-in replacement that preserves the *exact* old semantics: a **naive**
datetime whose wall-clock value is UTC. The DB columns are naive
`DateTime` (no `timezone=True`) and the poller compares timestamps assuming
naive UTC, so we deliberately strip the tzinfo rather than return an aware
datetime - mixing aware and naive values would raise TypeError on compare.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now - same as the deprecated `datetime.utcnow()`."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
