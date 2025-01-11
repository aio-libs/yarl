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


def calculate_relative_path(target: str, base: str) -> str:
    """Calculate the relative path between two other paths"""

    base_segments = base.split("/")[:-1]
    target_segments = target.split("/")

    offset = 0
    for base_seg, target_seg in zip(base_segments, target_segments):
        if base_seg == target_seg:
            offset += 1
        else:
            break

    remaining_base_segments = base_segments[offset:]
    remaining_target_segments = target_segments[offset:]

    relative_segments = [".."] * len(remaining_base_segments)
    relative_segments.extend(remaining_target_segments)

    return "/".join(relative_segments)
