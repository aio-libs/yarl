"""Tests for the in-tree PEP 517 build backend."""

import os
import shlex
import sys
import sysconfig
from pathlib import Path

import pytest
from pep517_backend._cython_configuration import patched_env
from setuptools._distutils.ccompiler import new_compiler
from setuptools._distutils.sysconfig import customize_compiler

RELEASE_FLAGS = ("-Ofast", "-g0", "-DNDEBUG")
TRACING_FLAGS = ("-Og", "--coverage", "-DCYTHON_TRACE=1", "-DCYTHON_TRACE_NOGIL=1")


def _interpreter_flags() -> list[str]:  # pragma: win32 no cover
    """Return the compiler flags CPython was configured with."""
    cflags: str = sysconfig.get_config_var("CFLAGS") or ""
    return shlex.split(cflags)


def _configured_compile_command() -> list[str]:  # pragma: win32 no cover
    """Return the compile command setuptools derives from the environment."""
    compiler = new_compiler()
    customize_compiler(compiler)
    # ``customize_compiler`` sets this attribute dynamically.
    command: list[str] = compiler.compiler_so  # type: ignore[attr-defined]
    return command


@pytest.mark.parametrize(
    ("tracing", "expected", "unexpected"),
    [(False, RELEASE_FLAGS, TRACING_FLAGS), (True, TRACING_FLAGS, RELEASE_FLAGS)],
)
def test_extra_flags_go_through_cppflags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tracing: bool,
    expected: tuple[str, ...],
    unexpected: tuple[str, ...],
) -> None:
    """Extra flags are appended to CPPFLAGS and CFLAGS is left alone.

    A CFLAGS environment variable replaces the interpreter's own compiler
    flags in setuptools' distutils, while CPPFLAGS is appended to them.
    """
    monkeypatch.setenv("CFLAGS", "-fuser-cflag")
    monkeypatch.setenv("CPPFLAGS", "-DUSER=1")
    source_dir = tmp_path / "src"
    build_dir = tmp_path / "build"

    with patched_env(
        {},
        cython_line_tracing_requested=tracing,
        original_source_directory=source_dir,
        temporary_build_directory=build_dir,
    ):
        cppflags = os.environ["CPPFLAGS"].split(" ")
        assert os.environ["CFLAGS"] == "-fuser-cflag"

    for flag in expected:
        assert flag in cppflags
    for flag in unexpected:
        assert flag not in cppflags
    assert f"-ffile-prefix-map={build_dir}={source_dir}" in cppflags
    # The user's own value keeps the top priority by coming last.
    assert cppflags[-1] == "-DUSER=1"
    assert os.environ["CPPFLAGS"] == "-DUSER=1"


@pytest.mark.skipif(  # pragma: win32 no cover
    sys.platform == "win32", reason="MSVC does not read CFLAGS or CPPFLAGS"
)
def test_interpreter_flags_survive_the_build_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The compiler still gets the interpreter's flags plus the extra ones.

    This drives setuptools' real compiler customization, so it fails if the
    backend ever goes back to setting CFLAGS.
    """
    # A developer shell exporting these would replace the flags up front.
    monkeypatch.delenv("CFLAGS", raising=False)
    monkeypatch.delenv("CPPFLAGS", raising=False)
    source_dir = tmp_path / "src"
    build_dir = tmp_path / "build"

    with patched_env(
        {},
        cython_line_tracing_requested=False,
        original_source_directory=source_dir,
        temporary_build_directory=build_dir,
    ):
        command = _configured_compile_command()

    for flag in _interpreter_flags():
        assert flag in command
    for flag in RELEASE_FLAGS:
        assert flag in command
    assert f"-ffile-prefix-map={build_dir}={source_dir}" in command
