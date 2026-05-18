"""Unit tests for the in-tree PEP 517 backend's ignore callback."""

import sys
from pathlib import Path

import pytest

_PACKAGING_DIR = Path(__file__).resolve().parents[1] / "packaging"


@pytest.fixture(scope="module")
def backend():
    sys.path.insert(0, str(_PACKAGING_DIR))
    try:
        from pep517_backend import _backend  # noqa: WPS433

        yield _backend
    finally:
        sys.path.remove(str(_PACKAGING_DIR))


def test_exclude_dir_path_filters_stale_native_artifacts(tmp_path, backend):
    (tmp_path / "stale.so").touch()
    (tmp_path / "stale.pyd").touch()
    (tmp_path / "stale.dylib").touch()
    (tmp_path / "keep.py").touch()
    contents = ["stale.so", "stale.pyd", "stale.dylib", "keep.py"]

    result = backend._exclude_dir_path(
        tmp_path.parent / "does-not-exist",
        str(tmp_path),
        contents,
    )

    assert sorted(result) == ["stale.dylib", "stale.pyd", "stale.so"]


def test_exclude_dir_path_keeps_directories_with_native_suffix(tmp_path, backend):
    (tmp_path / "looks_like.so").mkdir()
    (tmp_path / "real.py").touch()
    contents = ["looks_like.so", "real.py"]

    result = backend._exclude_dir_path(
        tmp_path.parent / "does-not-exist",
        str(tmp_path),
        contents,
    )

    assert result == []


def test_exclude_dir_path_filters_tempdir_parent(tmp_path, backend):
    tmpdir_parent = tmp_path / "build-tmp"
    tmpdir_parent.mkdir()
    (tmp_path / "keep.py").touch()
    contents = ["build-tmp", "keep.py"]

    result = backend._exclude_dir_path(
        tmpdir_parent,
        str(tmp_path),
        contents,
    )

    assert result == ["build-tmp"]


def test_exclude_dir_path_filters_both_categories(tmp_path, backend):
    tmpdir_parent = tmp_path / "build-tmp"
    tmpdir_parent.mkdir()
    (tmp_path / "stale.so").touch()
    (tmp_path / "keep.py").touch()
    contents = ["build-tmp", "stale.so", "keep.py"]

    result = backend._exclude_dir_path(
        tmpdir_parent,
        str(tmp_path),
        contents,
    )

    assert sorted(result) == ["build-tmp", "stale.so"]
