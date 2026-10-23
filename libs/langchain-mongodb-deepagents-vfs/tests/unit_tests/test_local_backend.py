"""Unit tests for LocalBackend.

STARTING POINT for the interview.
Copy to: libs/langchain-mongodb-deepagents-vfs/tests/unit_tests/test_local_backend.py

Each stage lists the tests to write FIRST (red), then the implementation (green).
Remove the skip marker as you reach each test. Model after test_s3_backend.py,
but use pytest's tmp_path instead of moto.
"""

from __future__ import annotations

import pytest

from langchain_mongodb_deepagents_vfs.backends.local import LocalBackend
from langchain_mongodb_deepagents_vfs.errors import AdapterError, ErrorCode


@pytest.fixture
def backend(tmp_path):
    return LocalBackend(tmp_path)


# ---- Stage 0 ---------------------------------------------------------------
@pytest.mark.unit
class TestLocalBackendInit:
    def test_missing_directory_raises(self, tmp_path):
        path = tmp_path / "nonexistent"
  
        with pytest.raises(AdapterError) as exc_info:
            LocalBackend(path)
        assert exc_info.value.code == ErrorCode.E1001_MISSING_CONFIG


# ---- Stage 1: path resolution ---------------------------------------------------
@pytest.mark.unit
class TestLocalBackendRootScope:
    # Drive through a public method (e.g. write or read), like
    # TestPrefixScopeEnforcement in test_s3_backend.py.
    def test_dotdot_traversal_is_refused(self, backend):
        # "../outside.txt" and "a/../../outside.txt" -> E2009
        outside_path = "../outside.txt"
        with pytest.raises(AdapterError) as exc_info:
            backend.write(outside_path, b"test") # should fail with E2009_PATH_OUTSIDE_PREFIX
        assert exc_info.value.code == ErrorCode.E2009_PATH_OUTSIDE_PREFIX

    def test_symlink_escape_is_refused(self, backend, tmp_path):
        # Create a file OUTSIDE tmp_path, symlink to it from inside, read it -> E2009
        outside_path = tmp_path / "../outside.txt"
        outside_path.touch()
        symlink_path = tmp_path / "symlink"
        symlink_path.symlink_to(outside_path)
        with pytest.raises(AdapterError) as exc_info:
            backend.read(symlink_path)
        assert exc_info.value.code == ErrorCode.E2009_PATH_OUTSIDE_PREFIX

    def test_leading_slash_is_relative_to_root(self, backend, tmp_path):
        # write("/a.txt") must land at <root>/a.txt, not at the filesystem root
        leading_slash_path = "/a.txt"
        with pytest.raises(AdapterError) as exc_info:
            backend.write(leading_slash_path, b"testinleadingslash")
        assert exc_info.value.code == ErrorCode.E2009_PATH_OUTSIDE_PREFIX



# ---- Stage 2: read side ------------------------------------------------------------
@pytest.mark.unit
class TestLocalBackendRead:
    def test_get_size(self, backend, tmp_path):
        # tmp_path = "/tmp/test"
        backend.write(tmp_path / "a.txt", b"test")
        assert backend.get_size(tmp_path / "a.txt") == 4

  


# ---- Stage 3: write side --------------------------------------------------------------
@pytest.mark.skip(reason="stage 3")
@pytest.mark.unit
class TestLocalBackendWrite:
    def test_write_then_read_creates_parent_dirs(self, backend, tmp_path):
        ...

    def test_write_overwrites(self, backend):
        ...

    def test_write_refuses_oversized_content(self, backend, monkeypatch):  # E2003
        ...


# ---- Stage 4: change detection ----------------------------------------------------------
@pytest.mark.skip(reason="stage 4")
@pytest.mark.unit
class TestLocalBackendListKeys:
    def test_lists_nested_files_as_posix_keys(self, backend):
        ...

    def test_prefix_filters(self, backend):
        ...



# ---- Stage 5: edit -----------------------------------------------------------------------
@pytest.mark.skip(reason="stage 5")
@pytest.mark.unit
class TestLocalBackendEdit:
    def test_edit_replaces_first_occurrence(self, backend):
        ...

    def test_edit_replace_all(self, backend):
        ...

    def test_edit_missing_raises(self, backend):  # E2001
        ...

    def test_edit_conflict_raises(self, backend, monkeypatch):
        # Simulate a concurrent change between read and write (hint: the etag
        # seen before the edit differs from the one seen just before the swap) -> E2008
        ...


# ---- Stage 6: bulk helpers ------------------------------------------------------------------
@pytest.mark.skip(reason="stage 6")
@pytest.mark.unit
class TestLocalBackendBulk:
    def test_upload_reports_per_path_errors(self, backend):
        # One good path, one "../bad.txt": expect one response each, in order,
        # with error set only on the bad one
        ...

    def test_download_reports_per_path_errors(self, backend):
        ...
