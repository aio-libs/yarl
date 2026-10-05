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
    "/": unlike normalize_path(), "a/../b" is "/b". The input buffer is
    path[pos:], so each step takes constant time apart from the segment it
    copies.
    """
    output: list[str] = []
    pos = 0
    end = len(path)
    while pos < end:
        if path.startswith("../", pos):
            pos += 3
        elif path.startswith(("./", "/./"), pos):
            pos += 2
        elif path.startswith("/../", pos):
            pos += 3
            if output:
                output.pop()
        elif end - pos == 2 and path.startswith("/.", pos):
            # "/." is replaced by "/", the last segment.
            output.append("/")
            break
        elif end - pos == 3 and path.startswith("/..", pos):
            # "/.." is replaced by "/" after dropping the previous segment.
            if output:
                output.pop()
            output.append("/")
            break
        elif end - pos <= 2 and path[pos:] in (".", ".."):
            break
        else:
            next_pos = path.find("/", pos + 1)
            if next_pos == -1:
                next_pos = end
            output.append(path[pos:next_pos])
            pos = next_pos
    return "".join(output)


# Windows drive letters in file URLs, as the WHATWG URL Standard reads them:
# https://url.spec.whatwg.org/#windows-drive-letter


def is_drive_letter(segment: str) -> bool:
    """Tell if segment is a Windows drive letter, as "C:" or "C|"."""
    return (
        len(segment) == 2
        and segment[1] in ":|"
        and segment[0].isascii()
        and segment[0].isalpha()
    )


def starts_with_drive_letter(path: str, pos: int = 0) -> bool:
    """Tell if path[pos:] starts with a Windows drive letter.

    The drive letter must be the whole first segment: "C:/a" and "C|" do,
    "C|a" does not.
    """
    return is_drive_letter(path[pos : pos + 2]) and (
        len(path) == pos + 2 or path[pos + 2] == "/"
    )


def drive_letter(path: str) -> str:
    """Return the normalized drive letter, as "C:", that path starts with.

    It is the first segment of an absolute or a rootless path, and the
    empty string when that is not a normalized drive letter.
    """
    pos = 1 if path[:1] == "/" else 0
    if starts_with_drive_letter(path, pos) and path[pos + 1] == ":":
        return path[pos : pos + 2]
    return ""


def normalize_drive_letter(path: str) -> str:
    """Write the "|" of a drive letter that starts an unquoted path as ":".

    The WHATWG path state does it only for the first segment, so "/C|/a" is
    "/C:/a" while "//C|/a" and "/a/C|" are kept.
    """
    pos = 1 if path[:1] == "/" else 0
    if starts_with_drive_letter(path, pos) and path[pos + 1] == "|":
        return f"{path[: pos + 1]}:{path[pos + 2 :]}"
    return path


def normalize_file_path(path: str) -> str:
    """Drop '.' and '..' from the path of a file URL, keeping its drive letter.

    As normalize_path(), except that '..' never removes a drive letter that
    is the first segment: the WHATWG "shorten a path" keeps "C:" in
    "/C:/.." and in "/C:/a/../..".
    """
    prefix = ""
    if path and path[0] == "/":
        prefix = "/"
        path = path[1:]
    segments = path.split("/")
    resolved: list[str] = []
    for seg in segments:
        if seg == "..":
            if resolved and not (len(resolved) == 1 and drive_letter(resolved[0])):
                resolved.pop()
        elif seg != ".":
            resolved.append(seg)
    if segments[-1] in (".", ".."):
        resolved.append("")
    return prefix + "/".join(resolved)
