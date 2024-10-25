"""Utilities for working with paths."""

from collections.abc import Generator, Sequence
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


class SimplePath:
    __slots__ = ("_tail", "_root", "_trailer", "normalized")

    def __init__(self, path: str, strip_root: bool = False) -> None:
        """Initialize a SimplePath object."""
        self._tail = [x for x in path.split("/") if x and x != "."]

        if strip_root:
            if path[-1] != "/" and len(self._tail) > 0:
                self._tail.pop()

        self._root = "/" if path[0] == "/" else ""
        self._trailer = "." if not path else ""
        self.normalized = self._root + "/".join(self._tail) or self._trailer

    @property
    def name(self) -> str:
        """Return the last part of the path."""
        return (self._tail[-1] if self._tail else "") or self._trailer

    @property
    def parts_count(self) -> int:
        """Return the number of parts in the path."""
        return len(self._tail) + bool(self._root)

    @property
    def parts(self):
        """An object providing sequence-like access to the
        components in the filesystem path."""
        if self._root:
            return (self._root,) + tuple(self._tail)
        return tuple(self._tail)

    def parents(self) -> Generator["SimplePath", None, None]:
        """Return a list of parent paths for a given path."""
        for i in range(len(self._tail) - 1, -1, -1):
            parent = object.__new__(SimplePath)
            parent._tail = self._tail[:i]
            parent._root = self._root
            parent._trailer = self._trailer
            parent.normalized = self._root + ("/".join(parent._tail) or self._trailer)
            yield parent


def calculate_relative_path(target: str, base: str) -> str:
    """Return the relative path between two other paths.

    If the operation is not possible, raise ValueError.
    """

    target = target or "/"
    base = base or "/"

    target_path = SimplePath(target)
    base_path = SimplePath(base, strip_root=True)

    target_path_parent_strs: Union[set[str], None] = None
    for step, path in enumerate(chain((base_path,), base_path.parents())):
        if path.normalized == target_path.normalized:
            break
        # If the target_path_parent_strs is already built use the quick path
        if target_path_parent_strs is not None:
            if path.normalized in target_path_parent_strs:
                break
            elif path.name == "..":
                raise ValueError(
                    f"'..' segment in {base_path.normalized!r} cannot be walked"
                )
            continue
        target_path_parent_strs = set()
        # We check one at a time because enumerating parents
        # builds the value on demand, and we want to stop
        # as soon as we find the common parent
        for parent in target_path.parents():
            if parent.normalized == base_path.normalized:
                break
            target_path_parent_strs.add(parent.normalized)
        else:
            # If we didn't break, it means we didn't find a common parent
            if path.name == "..":
                raise ValueError(
                    f"'..' segment in {base_path.normalized!r} cannot be walked"
                )
            continue
        break
    else:
        msg = (
            f"{target_path.normalized!r} and {base_path.normalized!r} "
            "have different anchors"
        )
        raise ValueError(msg)

    offset = path.parts_count
    return str(PurePosixPath(*("..",) * step, *target_path.parts[offset:]))
