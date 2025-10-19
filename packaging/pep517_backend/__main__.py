"""A command-line entry-point for the build backend helpers."""

import sys

from . import cli


if __name__ == '__main__':
    sys.exit(cli.run_main_program(argv=sys.argv))
