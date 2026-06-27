"""Unit tests for the in-tree PEP 517 backend's ignore callback."""

from pathlib import Path
from types import ModuleType

import pytest


@pytest.fixture(scope="module")
def backend() -> ModuleType:
    # The PEP 517 backend imports ``setuptools.build_meta`` and (transitively
    # via ``_cython_configuration``) ``expandvars`` at module load time.
    # Neither is present in the minimal cibuildwheel test venv that exercises
    # the built wheel, so skip cleanly if anyone runs the suite without the
    # full dev environment. The ``packaging/`` directory itself is placed on
    # the import path via the ``pythonpath`` setting in ``pytest.ini``.
    pytest.importorskip("setuptools")
    pytest.importorskip("expandvars")

    from pep517_backend import _backend  # noqa: PLC0415

    return _backend


def test_exclude_dir_path_filters_stale_native_artifacts(
    tmp_path: Path, backend: ModuleType
) -> None:
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


def test_exclude_dir_path_keeps_directories_with_native_suffix(
    tmp_path: Path, backend: ModuleType
) -> None:
    (tmp_path / "looks_like.so").mkdir()
    (tmp_path / "real.py").touch()
    contents = ["looks_like.so", "real.py"]

    result = backend._exclude_dir_path(
        tmp_path.parent / "does-not-exist",
        str(tmp_path),
        contents,
    )

    assert result == []


def test_exclude_dir_path_filters_tempdir_parent(
    tmp_path: Path, backend: ModuleType
) -> None:
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


def test_exclude_dir_path_filters_both_categories(
    tmp_path: Path, backend: ModuleType
) -> None:
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
