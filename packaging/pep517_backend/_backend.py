# fmt: off
"""PEP 517 build backend wrapper for pre-building Cython for wheel."""

from __future__ import annotations

import os
import typing as t
from contextlib import contextmanager, nullcontext, suppress
from functools import partial
from pathlib import Path
from shutil import copytree
from sys import implementation as _system_implementation
from sys import stderr as _standard_error_stream
from sys import version_info as _python_version_tuple
from tempfile import TemporaryDirectory
from warnings import warn as _warn_that

from setuptools.build_meta import build_sdist as _setuptools_build_sdist
from setuptools.build_meta import build_wheel as _setuptools_build_wheel
from setuptools.build_meta import (
    get_requires_for_build_wheel as _setuptools_get_requires_for_build_wheel,
)
from setuptools.build_meta import (
    prepare_metadata_for_build_wheel as _setuptools_prepare_metadata_for_build_wheel,
)

try:
    from setuptools.build_meta import build_editable as _setuptools_build_editable
except ImportError:
    _setuptools_build_editable = None  # type: ignore[assignment]


# isort: split
from distutils.command.install import install as _distutils_install_cmd
from distutils.core import Distribution as _DistutilsDistribution
from distutils.dist import DistributionMetadata as _DistutilsDistributionMetadata

with suppress(ImportError):
    # NOTE: Only available for wheel builds that bundle C-extensions. Declared
    # NOTE: by `get_requires_for_build_wheel()` and
    # NOTE: `get_requires_for_build_editable()`, when `pure-python`
    # NOTE: is not passed.
    from Cython.Build.Cythonize import main as _cythonize_cli_cmd

from ._compat import chdir_cm
from ._cython_configuration import (  # noqa: WPS436
    get_local_cython_config as _get_local_cython_config,
)
from ._cython_configuration import (
    make_cythonize_cli_args_from_config as _make_cythonize_cli_args_from_config,
)
from ._cython_configuration import patched_env as _patched_cython_env
from ._transformers import sanitize_rst_roles  # noqa: WPS436

__all__ = (  # noqa: WPS410
    'build_sdist',
    'build_wheel',
    'get_requires_for_build_wheel',
    'prepare_metadata_for_build_wheel',
    *(
        () if _setuptools_build_editable is None
        else (
            'build_editable',
            'get_requires_for_build_editable',
            'prepare_metadata_for_build_editable',
        )
    ),
)

_ConfigDict = t.Dict[str, t.Union[str, t.List[str], None]]


CYTHON_TRACING_CONFIG_SETTING = 'with-cython-tracing'
"""Config setting name toggle to include line tracing to C-exts."""

CYTHON_TRACING_ENV_VAR = 'YARL_CYTHON_TRACING'
"""Environment variable name toggle used to opt out of making C-exts."""

PURE_PYTHON_CONFIG_SETTING = 'pure-python'
"""Config setting name toggle that is used to opt out of making C-exts."""

PURE_PYTHON_ENV_VAR = 'YARL_NO_EXTENSIONS'
"""Environment variable name toggle used to opt out of making C-exts."""

IS_PY3_12_PLUS = _python_version_tuple[:2] >= (3, 12)
"""A flag meaning that the current runtime is Python 3.12 or higher."""

IS_CPYTHON = _system_implementation.name == "cpython"
"""A flag meaning that the current interpreter implementation is CPython."""

PURE_PYTHON_MODE_CLI_FALLBACK = not IS_CPYTHON
"""A fallback for ``pure-python`` is not set."""


def _is_truthy_setting_value(setting_value) -> bool:
    truthy_values = {'', None, 'true', '1', 'on'}
    return setting_value.lower() in truthy_values


def _get_setting_value(
        config_settings: _ConfigDict | None = None,
        config_setting_name: str | None = None,
        env_var_name: str | None = None,
        *,
        default: bool = False,
) -> bool:
    user_provided_setting_sources = (
        (config_settings, config_setting_name, (KeyError, TypeError)),
        (os.environ, env_var_name, KeyError),
    )
    for src_mapping, src_key, lookup_errors in user_provided_setting_sources:
        if src_key is None:
            continue

        with suppress(lookup_errors):  # type: ignore[arg-type]
            return _is_truthy_setting_value(src_mapping[src_key])  # type: ignore[index]

    return default


def _make_pure_python(config_settings: _ConfigDict | None = None) -> bool:
    return _get_setting_value(
        config_settings,
        PURE_PYTHON_CONFIG_SETTING,
        PURE_PYTHON_ENV_VAR,
        default=PURE_PYTHON_MODE_CLI_FALLBACK,
    )


def _include_cython_line_tracing(
        config_settings: _ConfigDict | None = None,
        *,
        default=False,
) -> bool:
    return _get_setting_value(
        config_settings,
        CYTHON_TRACING_CONFIG_SETTING,
        CYTHON_TRACING_ENV_VAR,
        default=default,
    )


@contextmanager
def patched_distutils_cmd_install():
    """Make `install_lib` of `install` cmd always use `platlib`.

    :yields: None
    """
    # Without this, build_lib puts stuff under `*.data/purelib/` folder
    orig_finalize = _distutils_install_cmd.finalize_options

    def new_finalize_options(self):  # noqa: WPS430
        self.install_lib = self.install_platlib
        orig_finalize(self)

    _distutils_install_cmd.finalize_options = new_finalize_options
    try:
        yield
    finally:
        _distutils_install_cmd.finalize_options = orig_finalize


@contextmanager
def patched_dist_has_ext_modules():
    """Make `has_ext_modules` of `Distribution` always return `True`.

    :yields: None
    """
    # Without this, build_lib puts stuff under `*.data/platlib/` folder
    orig_func = _DistutilsDistribution.has_ext_modules

    _DistutilsDistribution.has_ext_modules = lambda *args, **kwargs: True
    try:
        yield
    finally:
        _DistutilsDistribution.has_ext_modules = orig_func


@contextmanager
def patched_dist_get_long_description():
    """Make `has_ext_modules` of `Distribution` always return `True`.

    :yields: None
    """
    # Without this, build_lib puts stuff under `*.data/platlib/` folder
    _orig_func = _DistutilsDistributionMetadata.get_long_description

    def _get_sanitized_long_description(self):
        return sanitize_rst_roles(self.long_description)

    _DistutilsDistributionMetadata.get_long_description = (
        _get_sanitized_long_description
    )
    try:
        yield
    finally:
        _DistutilsDistributionMetadata.get_long_description = _orig_func


def _exclude_dir_path(
    excluded_dir_path: Path,
    visited_directory: str,
    _visited_dir_contents: list[str],
) -> list[str]:
    """Prevent recursive directory traversal."""
    # This stops the temporary directory from being copied
    # into self recursively forever.
    # Ref: https://github.com/aio-libs/yarl/issues/992
    visited_directory_subdirs_to_ignore = [
        subdir
        for subdir in _visited_dir_contents
        if excluded_dir_path == Path(visited_directory) / subdir
    ]
    if visited_directory_subdirs_to_ignore:
        print(
            f'Preventing `{excluded_dir_path !s}` from being '
            'copied into itself recursively...',
            file=_standard_error_stream,
        )
    return visited_directory_subdirs_to_ignore


@contextmanager
def _in_temporary_directory(src_dir: Path) -> t.Iterator[None]:
    with TemporaryDirectory(prefix='.tmp-yarl-pep517-') as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        root_tmp_dir_path = tmp_dir_path.parent
        _exclude_tmpdir_parent = partial(_exclude_dir_path, root_tmp_dir_path)

        with chdir_cm(tmp_dir):
            tmp_src_dir = tmp_dir_path / 'src'
            copytree(
                src_dir,
                tmp_src_dir,
                ignore=_exclude_tmpdir_parent,
                symlinks=True,
            )
            os.chdir(tmp_src_dir)
            yield


@contextmanager
def maybe_prebuild_c_extensions(
        line_trace_cython_when_unset: bool = False,
        build_inplace: bool = False,
        config_settings: _ConfigDict | None = None,
) -> t.Generator[None, t.Any, t.Any]:
    """Pre-build C-extensions in a temporary directory, when needed.

    This context manager also patches metadata, setuptools and distutils.

    :param build_inplace: Whether to copy and chdir to a temporary location.
    :param config_settings: :pep:`517` config settings mapping.

    """
    cython_line_tracing_requested = _include_cython_line_tracing(
        config_settings,
        default=line_trace_cython_when_unset,
    )
    is_pure_python_build = _make_pure_python(config_settings)

    if is_pure_python_build:
        print("*********************", file=_standard_error_stream)
        print("* Pure Python build *", file=_standard_error_stream)
        print("*********************", file=_standard_error_stream)

        if cython_line_tracing_requested:
            _warn_that(
                f'The `{CYTHON_TRACING_CONFIG_SETTING !s}` setting requesting '
                'Cython line tracing is set, but building C-extensions is not. '
                'This option will not have any effect for in the pure-python '
                'build mode.',
                RuntimeWarning,
                stacklevel=999,
            )

        yield
        return

    print("**********************", file=_standard_error_stream)
    print("* Accelerated build *", file=_standard_error_stream)
    print("**********************", file=_standard_error_stream)
    if not IS_CPYTHON:
        _warn_that(
            'Building C-extensions under the runtimes other than CPython is '
            'unsupported and will likely fail. Consider passing the '
            f'`{PURE_PYTHON_CONFIG_SETTING !s}` PEP 517 config setting.',
            RuntimeWarning,
            stacklevel=999,
        )

    build_dir_ctx = (
        nullcontext() if build_inplace
        else _in_temporary_directory(src_dir=Path.cwd().resolve())
    )
    with build_dir_ctx:
        config = _get_local_cython_config()

        cythonize_args = _make_cythonize_cli_args_from_config(config)
        with _patched_cython_env(config['env'], cython_line_tracing_requested):
            _cythonize_cli_cmd(cythonize_args)
        with patched_distutils_cmd_install():
            with patched_dist_has_ext_modules():
                yield


@patched_dist_get_long_description()
def build_wheel(
        wheel_directory: str,
        config_settings: _ConfigDict | None = None,
        metadata_directory: str | None = None,
) -> str:
    """Produce a built wheel.

    This wraps the corresponding ``setuptools``' build backend hook.

    :param wheel_directory: Directory to put the resulting wheel in.
    :param config_settings: :pep:`517` config settings mapping.
    :param metadata_directory: :file:`.dist-info` directory path.

    """
    with maybe_prebuild_c_extensions(
            line_trace_cython_when_unset=False,
            build_inplace=False,
            config_settings=config_settings,
    ):
        return _setuptools_build_wheel(
            wheel_directory=wheel_directory,
            config_settings=config_settings,
            metadata_directory=metadata_directory,
        )


@patched_dist_get_long_description()
def build_editable(
        wheel_directory: str,
        config_settings: _ConfigDict | None = None,
        metadata_directory: str | None = None,
) -> str:
    """Produce a built wheel for editable installs.

    This wraps the corresponding ``setuptools``' build backend hook.

    :param wheel_directory: Directory to put the resulting wheel in.
    :param config_settings: :pep:`517` config settings mapping.
    :param metadata_directory: :file:`.dist-info` directory path.

    """
    with maybe_prebuild_c_extensions(
            line_trace_cython_when_unset=True,
            build_inplace=True,
            config_settings=config_settings,
    ):
        return _setuptools_build_editable(
            wheel_directory=wheel_directory,
            config_settings=config_settings,
            metadata_directory=metadata_directory,
        )


def get_requires_for_build_wheel(
        config_settings: _ConfigDict | None = None,
) -> list[str]:
    """Determine additional requirements for building wheels.

    :param config_settings: :pep:`517` config settings mapping.

    """
    is_pure_python_build = _make_pure_python(config_settings)

    if not is_pure_python_build and not IS_CPYTHON:
        _warn_that(
            'Building C-extensions under the runtimes other than CPython is '
            'unsupported and will likely fail. Consider passing the '
            f'`{PURE_PYTHON_CONFIG_SETTING !s}` PEP 517 config setting.',
            RuntimeWarning,
            stacklevel=999,
        )

    c_ext_build_deps = [] if is_pure_python_build else [
        'Cython >= 3.0.0b3' if IS_PY3_12_PLUS  # Only Cython 3+ is compatible
        else 'Cython',
    ]

    return _setuptools_get_requires_for_build_wheel(
        config_settings=config_settings,
    ) + c_ext_build_deps


build_sdist = patched_dist_get_long_description()(_setuptools_build_sdist)
get_requires_for_build_editable = get_requires_for_build_wheel
prepare_metadata_for_build_wheel = patched_dist_get_long_description()(
    _setuptools_prepare_metadata_for_build_wheel,
)
prepare_metadata_for_build_editable = prepare_metadata_for_build_wheel
