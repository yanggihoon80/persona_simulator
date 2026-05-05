from __future__ import annotations

from pathlib import Path
from typing import Any

from utils import read_json_file, write_json_file


class JsonCache:
    def __init__(self, output_dir: str | Path = "output") -> None:
        self.output_dir = Path(output_dir)
        self.cache_key: str | None = None

    def set_cache_key(self, cache_key: str) -> None:
        self.cache_key = cache_key

    def path(self, filename: str) -> Path:
        return self.output_dir / filename

    def load_dict(self, filename: str) -> dict[str, Any]:
        path = self.path(filename)
        if not path.exists():
            return {}
        try:
            data = read_json_file(path)
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        if self.cache_key and data.get("_cache_key") != self.cache_key:
            return {}
        return data

    def load_list(self, filename: str, key: str) -> list[Any]:
        data = self.load_dict(filename)
        value = data.get(key, [])
        return value if isinstance(value, list) else []

    def save(self, filename: str, data: Any) -> None:
        if self.cache_key and isinstance(data, dict):
            data = {**data, "_cache_key": self.cache_key}
        write_json_file(self.path(filename), data)
