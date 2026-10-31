"""Append-only log key-value store. Values must be JSON serialisable."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterator, Optional

__all__ = ["KVStore"]


class KVStore:
    def __init__(self, path: str):
        self.path = path
        self._data: Dict[str, Any] = {}
        self._garbage = 0
        self._load()
        self._file = open(path, "a", encoding="utf-8")

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    break  # a torn final write; everything before it is intact
                self._apply(entry)

    def _apply(self, entry: Dict[str, Any]) -> None:
        key = entry["k"]
        if key in self._data:
            self._garbage += 1
        if entry.get("d"):
            self._data.pop(key, None)
            self._garbage += 1
        else:
            self._data[key] = entry["v"]

    def _append(self, entry: Dict[str, Any]) -> None:
        self._file.write(json.dumps(entry, separators=(",", ":")) + "\n")
        self._file.flush()
        os.fsync(self._file.fileno())
        self._apply(entry)

    def put(self, key: str, value: Any) -> None:
        self._append({"k": key, "v": value})

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        return self._data.get(key, default)

    def delete(self, key: str) -> bool:
        if key not in self._data:
            return False
        self._append({"k": key, "d": True})
        return True

    def keys(self) -> Iterator[str]:
        return iter(sorted(self._data))

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def compact(self) -> None:
        """Rewrite the log with only live entries, atomically."""
        self._file.close()
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for key in sorted(self._data):
                f.write(json.dumps({"k": key, "v": self._data[key]}, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)
        self._garbage = 0
        self._file = open(self.path, "a", encoding="utf-8")

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "KVStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
