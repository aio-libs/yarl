# fmt: off

from __future__ import annotations

import os
import typing as _t  # noqa: WPS111
from contextlib import contextmanager
from pathlib import Path
from sys import version_info as _python_version_tuple

from expandvars import expandvars

from ._compat import load_toml_from_string
from ._transformers import (
    get_cli_kwargs_from_config,
    get_enabled_cli_flags_from_config,
)


if _t.TYPE_CHECKING:
    import collections.abc as _c  # noqa: WPS111, WPS301


class Config(_t.TypedDict):
    """Data structure for the TOML config."""

    env: dict[str, str]
    flags: dict[str, bool]
    kwargs: dict[str, str | dict[str, str]]
    src: list[str]


def get_local_cython_config() -> Config:
    """Grab optional build dependencies from pyproject.toml config.

    :returns: config section from ``pyproject.toml``
    :rtype: dict

    This basically reads entries from::

        [tool.local.cython]
        # Env vars provisioned during cythonize call
        src = ["src/**/*.pyx"]

        [tool.local.cython.env]
        # Env vars provisioned during cythonize call
        LDFLAGS = "-lssh"

        [tool.local.cython.flags]
        # This section can contain the following booleans:
        # * annotate — generate annotated HTML page for source files
        # * build — build extension modules using distutils
        # * inplace — build extension modules in place using distutils (implies -b)
        # * force — force recompilation
        # * quiet — be less verbose during compilation
        # * lenient — increase Python compat by ignoring some compile time errors
        # * keep-going — compile as much as possible, ignore compilation failures
        annotate = false
        build = false
        inplace = true
        force = true
        quiet = false
        lenient = false
        keep-going = false

        [tool.local.cython.kwargs]
        # This section can contain args that have values:
        # * exclude=PATTERN      exclude certain file patterns from the compilation
        # * parallel=N    run builds in N parallel jobs (default: calculated per system)
        exclude = "**.py"
        parallel = 12

        [tool.local.cython.kwargs.directives]
        # This section can contain compiler directives
        # NAME = "VALUE"

        [tool.local.cython.kwargs.compile-time-env]
        # This section can contain compile time env vars
        # NAME = "VALUE"

        [tool.local.cython.kwargs.options]
        # This section can contain cythonize options
        # NAME = "VALUE"
    """
    config_toml_txt = (Path.cwd().resolve() / 'pyproject.toml').read_text()
    config_mapping = load_toml_from_string(config_toml_txt)
    return config_mapping['tool']['local']['cython']  # type: ignore[no-any-return]


def get_local_cythonize_config() -> Config:
    """Grab optional build dependencies from pyproject.toml config.

    :returns: config section from ``pyproject.toml``
    :rtype: dict

    This basically reads entries from::

        [tool.local.cythonize]
        # Env vars provisioned during cythonize call
        src = ["src/**/*.pyx"]

        [tool.local.cythonize.env]
        # Env vars provisioned during cythonize call
        LDFLAGS = "-lssh"

        [tool.local.cythonize.flags]
        # This section can contain the following booleans:
        # * annotate — generate annotated HTML page for source files
        # * build — build extension modules using distutils
        # * inplace — build extension modules in place using distutils (implies -b)
        # * force — force recompilation
        # * quiet — be less verbose during compilation
        # * lenient — increase Python compat by ignoring some compile time errors
        # * keep-going — compile as much as possible, ignore compilation failures
        annotate = false
        build = false
        inplace = true
        force = true
        quiet = false
        lenient = false
        keep-going = false

        [tool.local.cythonize.kwargs]
        # This section can contain args that have values:
        # * exclude=PATTERN      exclude certain file patterns from the compilation
        # * parallel=N    run builds in N parallel jobs (default: calculated per system)
        exclude = "**.py"
        parallel = 12

        [tool.local.cythonize.kwargs.directives]
        # This section can contain compiler directives
        # NAME = "VALUE"

        [tool.local.cythonize.kwargs.compile-time-env]
        # This section can contain compile time env vars
        # NAME = "VALUE"

        [tool.local.cythonize.kwargs.options]
        # This section can contain cythonize options
        # NAME = "VALUE"
    """
    config_toml_txt = (Path.cwd().resolve() / 'pyproject.toml').read_text()
    config_mapping = load_toml_from_string(config_toml_txt)
    return config_mapping['tool']['local']['cythonize']  # type: ignore[no-any-return]


def _configure_cython_line_tracing(
    config_kwargs: dict[str, str | dict[str, str]],
    *,
    cython_line_tracing_requested: bool,
) -> None:
    """Configure Cython line tracing directives if requested."""
    # If line tracing is requested, add it to the directives
    if cython_line_tracing_requested:
        directives = config_kwargs.setdefault('directive', {})
        assert isinstance(directives, dict)  # noqa: S101  # typing
        directives['linetrace'] = 'True'
        directives['profile'] = 'True'


def make_cythonize_cli_args_from_config(
    config: Config,
    *,
    cython_line_tracing_requested: bool = False,
) -> list[str]:
    """Compose ``cythonize`` CLI args from config."""
    py_ver_arg = f'-{_python_version_tuple.major!s}'

    cli_flags = get_enabled_cli_flags_from_config(config['flags'])
    config_kwargs = config['kwargs']

    _configure_cython_line_tracing(
        config_kwargs,
        cython_line_tracing_requested=cython_line_tracing_requested,
    )

    cli_kwargs = get_cli_kwargs_from_config(config_kwargs)

    return cli_flags + [py_ver_arg] + cli_kwargs + ['--'] + config['src']


@contextmanager
def patched_env(
    env: dict[str, str],
    *,
    cython_line_tracing_requested: bool,
    original_source_directory: Path | None = None,
    temporary_build_directory: Path | None = None,
) -> _c.Iterator[None]:
    """Temporary set given env vars.

    :param env: tmp env vars to set
    :type env: dict

    :yields: None
    """
    orig_env = os.environ.copy()
    expanded_env = {name: expandvars(var_val) for name, var_val in env.items()}  # type: ignore[no-untyped-call]
    os.environ.update(expanded_env)

    os.environ['CFLAGS'] = ' '.join((
        # First, low priority hardcoded value from the `pyproject.toml` config:
        expanded_env.get('CFLAGS', ''),
        # Next, add dynamically computed compiler flags:
        *(
            # Debug mode:
            (
                # Compiler-specific settings:
                '-g3',  # debug symbols w/ extra details
                '-Og',  # optimize for debug experience, better than -O0
                '-UNDEBUG',  # enable assertions
                # Coverage-related:
                '--coverage',
                # '-fkeep-inline-functions',  # clang seems to not support this
                # '-fkeep-static-functions',  # clang seems to not support this
                # '-fprofile-abs-path',  # clang seems to not support this
                # Cython-specific settings:
                '-DCYTHON_TRACE=1',
                '-DCYTHON_TRACE_NOGIL=1',
            )
            if cython_line_tracing_requested
            # Release mode:
            else (
                '-g0',  # no debug symbols
                '-Ofast',  # maximum optimization
                '-DNDEBUG',  # disable assertions
            )
        ),
        *(
            # In-tree mode:
            ()
            if temporary_build_directory is None
            # Temporary build directory mode:
            else (
                '-ffile-prefix-map='
                f'{temporary_build_directory!s}={original_source_directory!s}',
            )
        ),
        # Finally, append the user-set env var, ensuring its top priority:
        orig_env.get('CFLAGS', ''),
        # Last thing, strip spaces caused by empty leading/trailing flags:
    )).strip()

    os.environ['LDFLAGS'] = ' '.join((
        # First, low priority hardcoded value from the `pyproject.toml` config:
        expanded_env.get('LDFLAGS', ''),
        # Next, add dynamically computed linker flags:
        *(
            # Debug mode:
            (
                # Coverage-related:
                '--coverage',
            )
            if cython_line_tracing_requested
            # Release mode:
            else (
                '-s',  # remove all symbol table and relocation information
            )
        ),
        # Finally, append the user-set env var, ensuring its top priority:
        orig_env.get('LDFLAGS', ''),
        # Last thing, strip spaces caused by empty leading/trailing flags:
    )).strip()

    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(orig_env)
