"""Utilities for working with paths."""

from collections.abc import Sequence
from contextlib import suppress
from os.path import dirname, relpath

SEPARATOR = "/"


def normalize_path_segments(segments: Sequence[str]) -> list[str]:
    """Drop '.' and '..' from a sequence of str segments"""

    resolved_path: list[str] = []

    for seg in segments:
        if seg == "..":
            # ignore any .. segments that would otherwise cause an
            # IndexError when popped from resolved_path if
            # resolving for rfc3986
            with suppress(IndexError):
                resolved_path.pop()
        elif seg != ".":
            resolved_path.append(seg)

    if segments and segments[-1] in (".", ".."):
        # do some post-processing here.
        # if the last segment was a relative dir,
        # then we need to append the trailing '/'
        resolved_path.append("")

    return resolved_path


def normalize_path(path: str) -> str:
    # Drop '.' and '..' from str path
    prefix = ""
    if path and path[0] == SEPARATOR:
        # preserve the "/" root element of absolute paths, copying it to the
        # normalised output as per sections 5.2.4 and 6.2.2.3 of rfc3986.
        prefix = SEPARATOR
        path = path[1:]

    segments = path.split(SEPARATOR)
    return prefix + SEPARATOR.join(normalize_path_segments(segments))


def relative_path(path: str, start: str) -> str:
    """A wrapper over os.path.relpath()"""

    if not path:
        path = SEPARATOR
    if not start:
        start = SEPARATOR
    if not start.endswith(SEPARATOR):
        start = dirname(start)

    return relpath(path, start)
