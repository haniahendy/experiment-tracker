"""A tiny local experiment tracker for ML runs.

Runs are appended as JSON Lines to a store file; commands list, compare,
and pick the best run by any logged metric. No server, no database, no
dependencies: the store is a plain file you can commit or ignore.
"""

from .store import Run, RunStore
from .compare import best_run, compare_table

__all__ = ["Run", "RunStore", "best_run", "compare_table"]

__version__ = "0.1.0"
