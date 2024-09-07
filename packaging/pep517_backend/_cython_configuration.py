# fmt: off

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from sys import version_info as _python_version_tuple

from expandvars import expandvars

from ._compat import load_toml_from_string  # noqa: WPS436
from ._transformers import (  # noqa: WPS436
    get_cli_kwargs_from_config,
    get_enabled_cli_flags_from_config,
)


def get_local_cython_config() -> dict:
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
    return config_mapping['tool']['local']['cythonize']


def make_cythonize_cli_args_from_config(config) -> list[str]:
    py_ver_arg = f'-{_python_version_tuple.major!s}'

    cli_flags = get_enabled_cli_flags_from_config(config['flags'])
    cli_kwargs = get_cli_kwargs_from_config(config['kwargs'])

    return cli_flags + [py_ver_arg] + cli_kwargs + ['--'] + config['src']


@contextmanager
def patched_env(env: dict[str, str], cython_line_tracing_requested: bool):
    """Temporary set given env vars.

    :param env: tmp env vars to set
    :type env: dict

    :yields: None
    """
    orig_env = os.environ.copy()
    expanded_env = {name: expandvars(var_val) for name, var_val in env.items()}
    os.environ.update(expanded_env)

    if cython_line_tracing_requested:
        os.environ['CFLAGS'] = ' '.join((
            os.getenv('CFLAGS', ''),
            '-DCYTHON_TRACE_NOGIL=1',  # Implies CYTHON_TRACE=1
        )).strip()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(orig_env)
