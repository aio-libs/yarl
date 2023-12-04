# fmt: off

from __future__ import annotations

import sys
from itertools import chain
from pathlib import Path

from Cython.Compiler.Main import compile as _translate_cython_cli_cmd
from Cython.Compiler.Main import parse_command_line as _split_cython_cli_args

from ._cython_configuration import get_local_cython_config as _get_local_cython_config
from ._cython_configuration import (
    make_cythonize_cli_args_from_config as _make_cythonize_cli_args_from_config,
)
from ._cython_configuration import patched_env as _patched_cython_env

_PROJECT_PATH = Path(__file__).parents[2]


def run_main_program(argv) -> int | str:
    """Invoke ``translate-cython`` or fail."""
    if len(argv) != 2:
        return 'This program only accepts one argument -- "translate-cython"'

    if argv[1] != 'translate-cython':
        return 'This program only implements the "translate-cython" subcommand'

    config = _get_local_cython_config()
    config['flags'] = {'keep-going': config['flags']['keep-going']}
    config['src'] = list(
        map(
            str,
            chain.from_iterable(
                map(_PROJECT_PATH.glob, config['src']),
            ),
        ),
    )
    translate_cython_cli_args = _make_cythonize_cli_args_from_config(config)

    cython_options, cython_sources = _split_cython_cli_args(
        translate_cython_cli_args,
    )

    with _patched_cython_env(config['env'], cython_line_tracing_requested=True):
        return _translate_cython_cli_cmd(
            cython_sources,
            cython_options,
        ).num_errors


if __name__ == '__main__':
    sys.exit(run_main_program(argv=sys.argv))
