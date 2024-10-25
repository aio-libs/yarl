"""Utilities for working with paths."""

from collections.abc import Generator, Sequence
from contextlib import suppress
from itertools import chain
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


class URLPath:
    """A class for working with URL paths."""

    __slots__ = ("_tail", "_root", "path")

    def __init__(self, path: str, strip_tail: bool = False) -> None:
        """Initialize a URLPath object."""
        remove_tail = strip_tail and path and path[-1] != "/"
        root = "/" if path and path[0] == "/" else ""
        # Strip trailing slash
        if path and path[-1] == "/":
            path = path[:-1]
        if "." in path:
            # Strip '.' segments
            tail = [x for x in path.split("/") if x != "."]
        else:
            tail = path.split("/")
        if remove_tail and tail:
            tail.pop()
        self.path = (root + "/".join(tail)) or "."
        self._tail = tail
        self._root = root

    @property
    def name(self) -> str:
        """Return the last part of the path."""
        return self._tail[-1] if self._tail else ""

    @property
    def parts_count(self) -> int:
        """Return the number of parts in the path."""
        return len(self._tail) + bool(self._root)

    @property
    def parts(self) -> list[str]:
        """Return the parts of the path."""
        return [self._root, *self._tail] if self._root else self._tail

    def parents(self) -> Generator["URLPath", None, None]:
        """Return a list of parent paths for a given path."""
        root = self._root
        tail = self._tail
        for i in range(len(tail) - 1, -1, -1):
            parent_tail = tail[:i]
            url_path = object.__new__(URLPath)
            url_path.path = (root + "/".join(parent_tail)) or "."
            url_path._tail = parent_tail
            url_path._root = root
            yield url_path


def calculate_relative_path(target: str, base: str) -> str:
    """Return the relative path between two other paths.

    If the operation is not possible, raise ValueError.
    """
    target_path = URLPath(target or "/")
    base_path = URLPath(base or "/", strip_tail=True)

    target_path_parts: Union[set[str], None] = None
    target_path_path = target_path.path
    for step, base_walk in enumerate(chain((base_path,), base_path.parents())):
        if base_walk.path == target_path_path:
            break
        # If the target_path_parent_strs is already built use the quick path
        if target_path_parts is not None:
            if base_walk.path in target_path_parts:
                break
            elif base_walk.name == "..":
                raise ValueError(f"'..' segment in {base_path.path!r} cannot be walked")
            continue
        target_path_parts = set()
        # We check one at a time because enumerating parents
        # builds the value on demand, and we want to stop
        # as soon as we find the common parent
        for parent in target_path.parents():
            if parent.path == base_path.path:
                break
            target_path_parts.add(parent.path)
        else:
            # If we didn't break, it means we didn't find a common parent
            if base_walk.name == "..":
                raise ValueError(f"'..' segment in {base_path.path!r} cannot be walked")
            continue
        break
    else:
        msg = f"{target_path_path!r} and {base_path.path!r} have different anchors"
        raise ValueError(msg)

    return (
        "/".join((*("..",) * step, *target_path.parts[base_walk.parts_count :])) or "."
    )
