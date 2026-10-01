"""Utilities for working with paths."""

from collections.abc import Sequence
from contextlib import suppress


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


def remove_dot_segments(path: str) -> str:
    """Remove '.' and '..' as the remove_dot_segments algorithm does.

    The steps of RFC 3986 section 5.2.4, also for a path without a leading
    "/": unlike normalize_path(), "a/../b" is "/b".
    """
    output: list[str] = []
    while path:
        if path.startswith("../"):
            path = path[3:]
        elif path.startswith(("./", "/./")):
            path = path[2:]
        elif path.startswith("/../"):
            path = path[3:]
            if output:
                output.pop()
        elif path == "/.":
            path = "/"
        elif path == "/..":
            path = "/"
            if output:
                output.pop()
        elif path in (".", ".."):
            path = ""
        else:
            end = path.find("/", 1)
            if end == -1:
                end = len(path)
            output.append(path[:end])
            path = path[end:]
    return "".join(output)
