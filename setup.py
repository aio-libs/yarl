import os
import pathlib
import re
import sys

from setuptools import Extension, setup

NO_EXTENSIONS = bool(os.environ.get("YARL_NO_EXTENSIONS"))  # type: bool

if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


extensions = [Extension("yarl._quoting_c", ["yarl/_quoting_c.c"])]


here = pathlib.Path(__file__).parent


def read(name):
    fname = here / name
    with fname.open(encoding="utf8") as f:
        return f.read()


# $ echo ':something:`test <sdf>`' | sed 's/:\w\+:`\(\w\+\)\(\s\+\(.*\)\)\?`/``\1``/g'
# ``test``
def sanitize_rst_roles(rst_source_text: str) -> str:
    """Replace RST roles with inline highlighting."""
    role_regex = r":\w+:`(?P<rendered_text>[^`]+)(\s+(.*))?`"
    substitution_pattern = r"``(?P=rendered_text)``"
    return re.sub(role_regex, substitution_pattern, rst_source_text)


args = dict(
    long_description="\n\n".join(
        [read("README.rst"), sanitize_rst_roles(read("CHANGES.rst"))]
    ),
)


if not NO_EXTENSIONS:
    print("**********************")
    print("* Accelerated build *")
    print("**********************")
    setup(ext_modules=extensions, **args)
else:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    setup(**args)
