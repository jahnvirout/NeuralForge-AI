from collections import OrderedDict
from pathlib import Path
import shutil
import tempfile
import threading
import time
from typing import Any, Dict, Optional


class RepoCache:
    """
    In-memory bounded cache for cloned git repositories.
    Guarantees:
      - Max 2 cached repositories.
      - 30-minute TTL per repository from last access.
      - Evicted or expired directories are removed from disk.
      - System cache directory cleared on application startup.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_repos: int = 2,
        ttl_seconds: int = 1800,  # 30 minutes
        clear_on_init: bool = True,
    ):
        self.cache_dir = cache_dir or (Path(tempfile.gettempdir()) / "neuralforge_repo_cache")
        self.max_repos = max_repos
        self.ttl = ttl_seconds
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        if clear_on_init:
            self.clear_all_disk()

    def clear_all_disk(self) -> None:
        """Cleans disk cache directory on startup."""
        with self._lock:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir, ignore_errors=True)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._entries.clear()

    def _cleanup_expired_locked(self) -> None:
        now = time.time()
        expired_keys = [
            k for k, entry in self._entries.items()
            if (now - entry["last_accessed"]) >= self.ttl
        ]
        for k in expired_keys:
            entry = self._entries.pop(k)
            shutil.rmtree(entry["path"], ignore_errors=True)

    def get(self, url: str) -> Optional[str]:
        """Returns cached directory path if present and valid; updates last_accessed."""
        normalized = url.strip().rstrip("/").lower()
        with self._lock:
            self._cleanup_expired_locked()
            if normalized in self._entries:
                entry = self._entries[normalized]
                if Path(entry["path"]).exists():
                    entry["last_accessed"] = time.time()
                    self._entries.move_to_end(normalized)
                    return entry["path"]
                else:
                    self._entries.pop(normalized, None)
            return None

    def allocate_repo_dir(self, url: str) -> str:
        """Creates and returns a new directory path inside the cache directory."""
        import uuid
        normalized = url.strip().rstrip("/").lower()
        slug = "".join(c if c.isalnum() else "_" for c in normalized[-30:])
        unique_name = f"{slug}_{uuid.uuid4().hex[:8]}"
        dest = self.cache_dir / unique_name
        dest.mkdir(parents=True, exist_ok=True)
        return str(dest)

    def put(self, url: str, path: str) -> None:
        """Stores a cloned directory in cache, evicting oldest if max_repos exceeded."""
        normalized = url.strip().rstrip("/").lower()
        with self._lock:
            self._cleanup_expired_locked()

            # Evict oldest if reaching capacity
            while len(self._entries) >= self.max_repos and normalized not in self._entries:
                _, oldest_entry = self._entries.popitem(last=False)
                shutil.rmtree(oldest_entry["path"], ignore_errors=True)

            self._entries[normalized] = {
                "path": str(Path(path).resolve()),
                "last_accessed": time.time(),
                "created_at": time.time(),
            }
            self._entries.move_to_end(normalized)

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


# Global singleton instance for backend
repo_cache = RepoCache()
