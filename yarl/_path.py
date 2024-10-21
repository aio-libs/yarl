"""Utilities for working with paths."""

from collections.abc import Sequence
from contextlib import suppress
from os.path import dirname, relpath


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
    if path and path[0] == "/":
        # preserve the "/" root element of absolute paths, copying it to the
        # normalised output as per sections 5.2.4 and 6.2.2.3 of rfc3986.
        prefix = "/"
        path = path[1:]

    segments = path.split("/")
    return prefix + "/".join(normalize_path_segments(segments))


def calculate_relative_path(path: str, start: str) -> str:
    """A wrapper over os.path.relpath()"""

    if not path:
        path = "/"
    if not start:
        start = "/"
    if not start.endswith("/"):
        start = dirname(start)

    path_has_leading_slash = path.startswith("/")
    start_has_leading_slash = start.startswith("/")
    both_have_leading_slash = all((path_has_leading_slash, start_has_leading_slash))
    none_have_leading_slash = all(
        (not path_has_leading_slash, not start_has_leading_slash)
    )
    if not both_have_leading_slash and not none_have_leading_slash:
        raise ValueError(
            "It is forbidden to get the path between the absolute and relative paths "
            "because it is impossible to get the current working directory."
        )

    return relpath(path, start)
