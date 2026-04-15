"""Parquet-backed disk cache so API calls are never repeated across runs."""
import json
import hashlib
from pathlib import Path
from typing import Any, Optional
import threading

import pandas as pd


class ParquetCache:
    """Simple key→JSON cache backed by a Parquet file.

    Keys are arbitrary strings; values are JSON-serializable dicts.
    The backing file is rewritten on every flush() call (call after batches).
    """

    def __init__(self, path: Path):
        self.path = path
        self._store: dict[str, Any] = {}
        self._lock = threading.RLock()
        if path.exists():
            df = pd.read_parquet(path)
            self._store = {row["key"]: json.loads(row["value"]) for _, row in df.iterrows()}

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = value

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    def flush(self) -> None:
        with self._lock:
            items = list(self._store.items())
        rows = [{"key": k, "value": json.dumps(v)} for k, v in items]
        if rows:
            pd.DataFrame(rows).to_parquet(self.path, index=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
