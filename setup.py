import pathlib
import re

from setuptools import setup

here = pathlib.Path(__file__).parent
fname = here / 'yarl' / '__init__.py'

with fname.open() as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

install_requires = ['multidict>=2.0']


def read(name):
    fname = here / name
    with fname.open() as f:
        return f.read()


setup(name='yarl',
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
          'Topic :: Internet :: WWW/HTTP'],
      author='Andrew Svetlov',
      author_email='andrew.svetlov@gmail.com',
      url='https://github.com/aio-libs/yarl/',
      license='Apache 2',
      packages=['yarl'],
      install_requires=install_requires,
      include_package_data=True)
