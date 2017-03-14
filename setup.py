import pathlib
import sys
import re

from setuptools import setup, Extension
from distutils.errors import (CCompilerError, DistutilsExecError,
                              DistutilsPlatformError)
from distutils.command.build_ext import build_ext


try:
    from Cython.Build import cythonize
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

ext = '.pyx' if USE_CYTHON else '.c'

extensions = [Extension('yarl._quoting',
                        ['yarl/_quoting' + ext],)]
# extra_compile_args=["-g"],
# extra_link_args=["-g"],


if USE_CYTHON:
    extensions = cythonize(extensions)


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
        except (CCompilerError, DistutilsExecError,
                DistutilsPlatformError, ValueError):
            raise BuildFailed()


here = pathlib.Path(__file__).parent
fname = here / 'yarl' / '__init__.py'

with fname.open(encoding='utf8') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

install_requires = ['multidict>=2.0']

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
if needs_pytest:
    setup_requires = ['pytest-runner']
else:
    setup_requires = []


def read(name):
    fname = here / name
    with fname.open(encoding='utf8') as f:
        return f.read()


args = dict(
    name='yarl',
    version=version,
    description=("Yet another URL library"),
    long_description='\n\n'.join([read('README.rst'),
                                  read('CHANGES.rst')]),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP'],
    author='Andrew Svetlov',
    author_email='andrew.svetlov@gmail.com',
    url='https://github.com/aio-libs/yarl/',
    license='Apache 2',
    packages=['yarl'],
    install_requires=install_requires,
    include_package_data=True,
    setup_requires=setup_requires,
    tests_require=['pytest'],
    ext_modules=extensions,
    cmdclass=dict(build_ext=ve_build_ext))


try:
    setup(**args)
except BuildFailed:
    print("************************************************************")
    print("Cannot compile C accelerator module, use pure python version")
    print("************************************************************")
    del args['ext_modules']
    del args['cmdclass']
    setup(**args)
