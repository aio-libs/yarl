"""Utilities for working with paths."""

from collections.abc import Sequence
from contextlib import suppress
from itertools import chain
from pathlib import PurePosixPath
from typing import Union


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

    if base[-1] != "/":
        base_path = base_path.parent

    target_path_parent_strs: Union[set[str], None] = None
    target_path_str = str(target_path)
    base_path_str = str(base_path)
    for step, path in enumerate(chain((base_path,), base_path.parents)):
        if (path_str := str(path)) == target_path_str:
            break
        # If the target_path_parent_strs is already built use the quick path
        if target_path_parent_strs is not None:
            if path_str in target_path_parent_strs:
                break
            elif path.name == "..":
                raise ValueError(f"'..' segment in {base_path_str!r} cannot be walked")
            continue
        target_path_parent_strs = set()
        # We check one at a time because enumerating parents
        # builds the value on demand, and we want to stop
        # as soon as we find the common parent
        for parent in target_path.parents:
            if (parent_str := str(parent)) == base_path_str:
                break
            target_path_parent_strs.add(parent_str)
        else:
            # If we didn't break, it means we didn't find a common parent
            if path.name == "..":
                raise ValueError(f"'..' segment in {base_path_str!r} cannot be walked")
            continue
        break
    else:
        raise ValueError(
            f"{target_path_str!r} and {base_path_str!r} have different anchors"
        )
    offset = len(path.parts)
    return str(PurePosixPath(*("..",) * step, *target_path.parts[offset:]))
