"""
Transparent local/S3 cache for ilhmp intermediates.

Usage:
    cache = Cache("s3://ilhmp-data/")       # S3-backed
    cache = Cache("/data/cache")             # local dir
    cache = Cache(None)                      # no-op (disabled)

    # Check + fetch
    if cache.exists("dem/lake/lake_dtm.tif"):
        cache.pull("dem/lake/lake_dtm.tif", local_path)

    # Upload after generating
    cache.push(local_path, "dem/lake/lake_dtm.tif")
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Union


class Cache:
    """Unified local/S3 cache interface."""

    def __init__(self, root: Optional[Union[str, Path]]):
        if root is None:
            self._mode = "disabled"
            self._root = None
        elif str(root).startswith("s3://"):
            self._mode = "s3"
            self._root = str(root).rstrip("/")
        else:
            self._mode = "local"
            self._root = Path(root)
            self._root.mkdir(parents=True, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return self._mode != "disabled"

    @property
    def is_s3(self) -> bool:
        return self._mode == "s3"

    def _resolve(self, key: str) -> str:
        """Resolve a cache key to a full path/URI."""
        if self._mode == "s3":
            return f"{self._root}/{key}"
        elif self._mode == "local":
            return str(self._root / key)
        return ""

    def exists(self, key: str) -> bool:
        """Check if a cached artifact exists."""
        if self._mode == "disabled":
            return False

        if self._mode == "s3":
            result = subprocess.run(
                ["aws", "s3", "ls", self._resolve(key)],
                capture_output=True, text=True,
            )
            return result.returncode == 0 and len(result.stdout.strip()) > 0

        return Path(self._resolve(key)).exists()

    def pull(self, key: str, local_path: Path) -> bool:
        """
        Download a cached artifact to a local path.

        Returns True if successful, False if not found or failed.
        """
        if self._mode == "disabled":
            return False

        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        if self._mode == "s3":
            result = subprocess.run(
                ["aws", "s3", "cp", self._resolve(key), str(local_path)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(f"\u23e9 Cache hit (S3): {key}")
                return True
            return False

        src = Path(self._resolve(key))
        if src.exists():
            if src != local_path:
                shutil.copy2(src, local_path)
            print(f"\u23e9 Cache hit (local): {key}")
            return True
        return False

    def push(self, local_path: Path, key: str) -> bool:
        """
        Upload a local file to the cache.

        Returns True if successful.
        """
        if self._mode == "disabled":
            return False

        local_path = Path(local_path)
        if not local_path.exists():
            return False

        if self._mode == "s3":
            result = subprocess.run(
                ["aws", "s3", "cp", str(local_path), self._resolve(key)],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(f"\U0001f4be Cached (S3): {key}")
                return True
            else:
                print(f"\u26a0\ufe0f  S3 upload failed: {result.stderr.strip()}")
                return False

        dst = Path(self._resolve(key))
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst != local_path:
            shutil.copy2(local_path, dst)
        print(f"\U0001f4be Cached (local): {key}")
        return True

    def __repr__(self):
        return f"Cache({self._mode}:{self._root})"
