"""Utilities for working with paths."""

from collections.abc import Sequence
from contextlib import suppress
from itertools import chain
from pathlib import PurePosixPath
from typing import Union
from collections.abc import Generator


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


class SimplePath:

    __slots__ = ("parts", "root", "trailer", "normalized")

    def __init__(self, path: str, strip_root: bool = False) -> None:
        """Initialize a SimplePath object."""
        self.parts = [x for x in path.split("/") if x and x != "."]

        if strip_root:
            if path[-1] != "/" and len(self.parts) > 0:
                self.parts.pop()

        self.root = "/" if path[0] == "/" else ""
        self.trailer = "." if not path else ""
        self.normalized = self.root + "/".join(self.parts) or self.trailer

    def parents(self) -> Generator[str, None, None]:
        """Return a list of parent paths for a given path."""
        for i in range(len(self.parts) - 1, -1, -1):
            yield self.root + ("/".join(self.parts[:i]) or self.trailer)


def calculate_relative_path(target: str, base: str) -> str:
    """Return the relative path between two other paths.

    If the operation is not possible, raise ValueError.
    """

    target = target or "/"
    base = base or "/"

    target_path = SimplePath(target)
    base_path = SimplePath(base, strip_root=True)

    target_path_parent_strs: Union[set[str], None] = None
    for step, path_str in enumerate(
        chain((base_path.normalized,), base_path.parents())
    ):
        if path_str == target_path.normalized:
            break
        # If the target_path_parent_strs is already built use the quick path
        if target_path_parent_strs is not None:
            if path_str in target_path_parent_strs:
                break
            elif (
                path_str
                and path_str[-1] == "."
                and len(path_str) > 1
                and path_str[-2] == "."
            ):
                raise ValueError(
                    f"'..' segment in {base_path.normalized!r} cannot be walked"
                )
            continue
        target_path_parent_strs = set()
        # We check one at a time because enumerating parents
        # builds the value on demand, and we want to stop
        # as soon as we find the common parent
        for parent in target_path.parents():
            if parent == base_path.normalized:
                break
            target_path_parent_strs.add(parent)
        else:
            # If we didn't break, it means we didn't find a common parent
            if (
                path_str
                and path_str[-1] == "."
                and len(path_str) > 1
                and path_str[-2] == "."
            ):
                raise ValueError(
                    f"'..' segment in {base_path.normalized!r} cannot be walked"
                )
            continue
        break
    else:
        raise ValueError(
            f"{target_path.normalized!r} and {base_path.normalized!r} have different anchors"
        )
    offset = len(PurePosixPath(path_str).parts)
    return str(
        PurePosixPath(
            *("..",) * step, *PurePosixPath(target_path.normalized).parts[offset:]
        )
    )
