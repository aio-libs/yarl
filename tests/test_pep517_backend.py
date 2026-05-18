"""Unit tests for the in-tree PEP 517 backend's ignore callback."""

import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

_PACKAGING_DIR = Path(__file__).resolve().parents[1] / "packaging"


@pytest.fixture(scope="module")
def backend() -> Iterator[ModuleType]:
    # The PEP 517 backend imports ``setuptools.build_meta`` at module load
    # time, which is not available in the minimal cibuildwheel test venv
    # that exercises the built wheel.
    pytest.importorskip("setuptools")

    sys.path.insert(0, str(_PACKAGING_DIR))
    try:
        # The in-tree backend lives under packaging/ rather than on the
        # default import path, so it can only be resolved after the
        # directory has been prepended to sys.path above.
        from pep517_backend import _backend  # noqa: PLC0415

        yield _backend
    finally:
        sys.path.remove(str(_PACKAGING_DIR))


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
