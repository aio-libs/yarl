import pathlib
import os
import sys
import re

from setuptools import setup, Extension
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
from distutils.command.build_ext import build_ext


NO_EXTENSIONS = bool(os.environ.get("YARL_NO_EXTENSIONS"))  # type: bool

if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


extensions = [Extension("yarl._quoting", ["yarl/_quoting.c"])]
# extra_compile_args=["-g"],
# extra_link_args=["-g"],


class BuildFailed(Exception):
    pass


class ve_build_ext(build_ext):
    # This class allows C extension building to fail.

    def run(self):
        try:
            build_ext.run(self)
        except (DistutilsPlatformError, FileNotFoundError):
            raise BuildFailed()

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError, DistutilsPlatformError, ValueError):
            raise BuildFailed()


here = pathlib.Path(__file__).parent
fname = here / "yarl" / "__init__.py"

with fname.open(encoding="utf8") as fp:
    try:
        version = re.findall(r'^__version__ = "([^"]+)"$', fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")

install_requires = ["multidict>=4.0", "idna>=2.0"]

needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
if needs_pytest:
    setup_requires = ["pytest-runner"]
else:
    setup_requires = []


def read(name):
    fname = here / name
    with fname.open(encoding="utf8") as f:
        return f.read()


args = dict(
    name="yarl",
    version=version,
    description=("Yet another URL library"),
    long_description="\n\n".join([read("README.rst"), read("CHANGES.rst")]),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
    ],
    author="Andrew Svetlov",
    author_email="andrew.svetlov@gmail.com",
    url="https://github.com/aio-libs/yarl/",
    license="Apache 2",
    packages=["yarl"],
    install_requires=install_requires,
    python_requires=">=3.5.3",
    include_package_data=True,
    setup_requires=setup_requires,
    tests_require=["pytest"],
)


if not NO_EXTENSIONS:
    print("**********************")
    print("* Accellerated build *")
    print("**********************")
    setup(ext_modules=extensions, cmdclass=dict(build_ext=ve_build_ext), **args)
else:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    setup(**args)
