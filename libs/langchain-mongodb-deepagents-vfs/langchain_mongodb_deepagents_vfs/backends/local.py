"""Local filesystem backend.

STARTING POINT for the interview.
Copy to: libs/langchain-mongodb-deepagents-vfs/langchain_mongodb_deepagents_vfs/backends/local.py

Work through the stages in order. Each stub is marked with its stage number;
a stage is done when its tests (test_local_backend.py) pass.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from langchain_mongodb_deepagents_vfs.backends.base import (
    MAX_READ_BYTES,
    ObjectStoreBackend,
)
from langchain_mongodb_deepagents_vfs.errors import AdapterError, ErrorCode


class LocalBackend(ObjectStoreBackend):
    """ObjectStoreBackend backed by a directory on the local disk.

    Keys are POSIX paths relative to *root*: ``docs/a.md`` is ``<root>/docs/a.md``.
    The root is the isolation boundary (S3Backend's ``prefix`` plays this role).
    """

    # ---- Stage 0: skeleton -------------------------------------------------
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root).resolve()
        if not self.root.is_dir():
            raise AdapterError(ErrorCode.E1001_MISSING_CONFIG, "root is not a directory")
       
        
    # ---- Stage 1: path resolution (security) ------------------------------
    def _resolve(self, path: str) -> Path:
        """Map an untrusted key to a real path inside the root.

        Hint: compare S3Backend._key(). Which Path methods collapse ``..`` and
        follow symlinks? Do that BEFORE the containment check.
        Raise AdapterError(E2009_PATH_OUTSIDE_PREFIX) when it escapes.
        """

        normalized_path = Path(path).resolve()
        #check whether normalized_path is a child of self.root
        if not normalized_path.is_relative_to(self.root):
            raise AdapterError(ErrorCode.E2009_PATH_OUTSIDE_PREFIX, "path is outside the root")
        return normalized_path

    # ---- Stage 2: read side -------------------------------------------------
    def get_size(self, path: str) -> int:
        """Size in bytes. E2001 if missing, E2002 for other OSErrors."""
        try:
            resolved_path = self._resolve(path)
            size = resolved_path.stat().st_size
        except OSError as e:
            raise AdapterError(ErrorCode.E2002_OBJECT_READ_FAILED, e.strerror) from e
        return size

    def read(self, path: str, offset: int = 0, limit: int = -1) -> bytes:
        """Bytes of *path*, sliced by byte offset / limit.

        Must never materialise more than MAX_READ_BYTES (raise E2002).
        Hint: how can you detect "too big" without reading the whole file?
        """
        resolved_path = self._resolve(path)
        if resolved_path.stat().st_size > MAX_READ_BYTES:
            raise AdapterError(ErrorCode.E2002_OBJECT_READ_FAILED, "path is too large")
        with resolved_path.open("rb") as f:
            f.seek(offset)
            return f.read(limit)

    # ---- Stage 3: write side --------------------------------------------------
    def write(self, path: str, content: bytes) -> None:
        """Create or replace *path*, creating parent directories.

        Refuse content larger than MAX_READ_BYTES (E2003): never store what
        read() would refuse. Wrap OSError as E2003.
        Think: the watcher polls at any moment. Can it see a half-written file?
        """
        resolved_path = self._resolve(path)
        if len(content) > MAX_READ_BYTES:
            raise AdapterError(ErrorCode.E2003_OBJECT_WRITE_FAILED, "content is too large")
        resolved_path.write_bytes(content)
        

    # ---- Stage 4: change detection ---------------------------------------------
    def get_etag(self, key: str) -> str | None:
        """Current etag for *key*, or None if it does not exist.

        The watcher finds this with getattr(store, "get_etag", ...).
        """
        raise NotImplementedError

    def list_keys(self, prefix: str = "") -> Iterator[tuple[str, str]]:
        """Yield (key, etag) for every file whose key starts with *prefix*.

        Keys are POSIX-style and relative to the root, even on Windows.
        Wrap OSError as E2005. PollingWatcher diffs this output.
        """
        raise NotImplementedError

    # ---- Stage 5: edit -----------------------------------------------------------
    def edit(self, path: str, old: str, new: str, replace_all: bool = False) -> int:
        """Replace *old* with *new*; return the occurrences replaced.

        S3 uses If-Match for E2008 (conflict). The local disk has no such thing:
        what can you compare, and when, to detect a concurrent change?
        """
        raise NotImplementedError

    # ---- Stage 6: bulk helpers ----------------------------------------------------
    # upload_files / download_files are abstract in the ABC in the unmodified repo.
    # Implement them, compare with S3Backend, then refactor (see stage 6 notes).
    def upload_files(self, files):  # type: ignore[no-untyped-def]
        raise NotImplementedError

    def download_files(self, paths):  # type: ignore[no-untyped-def]
        raise NotImplementedError
