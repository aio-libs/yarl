"""Utilities for working with paths."""

import sys
from collections.abc import Sequence
from contextlib import suppress
from pathlib import PurePosixPath


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


def calculate_relative_path(target: str, base: str) -> str:
    """Return the relative path between two other paths.

    If the operation is not possible, raise ValueError.
    """

    target = target or "/"
    base = base or "/"

    target_path = PurePosixPath(target)
    base_path = PurePosixPath(base)

    if not base[-1] == "/":
        base_path = base_path.parent

    if sys.version_info >= (3, 12):
        return str(target_path.relative_to(base_path, walk_up=True))

    for step, path in enumerate((base_path, *base_path.parents)):
        if target_path.is_relative_to(path):
            break
        elif path.name == "..":
            raise ValueError(f"'..' segment in {str(base_path)!r} cannot be walked")
    else:
        raise ValueError(
            f"{str(target_path)!r} and {str(base_path)!r} have different anchors"
        )
    offset = len(path.parts)
    return str(PurePosixPath(*("..",) * step, *target_path.parts[offset:]))
