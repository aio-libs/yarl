.. yarl documentation master file, created by
   sphinx-quickstart on Mon Aug 29 19:55:36 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

yarl
====

The module provides handy :class:`~yarl.URL` class for url parsing and
manipulating.

Introduction
------------

Url could be constructed from :class:`str`::

   >>> from yarl import URL
   >>> url = URL('https://www.python.org/~guido?arg=1#frag')
   >>> url
   URL('https://www.python.org/~guido?arg=1#frag')

All url parts: scheme, host, port, path, query and fragment are
accessible by properties::

   >>> url.scheme
   'https'
   >>> url.host
   'www.python.org'
   >>> url.path
   '/~guido'
   >>> url.query_string
   'arg=1'
   >>> url.query
   <MultiDictProxy('arg': '1')>
   >>> url.fragment
   'frag'

All url manipulations produces a new url object::

   >>> url.parent / 'downloads/source'
   URL('https://www.python.org/downloads/source')

Strings in :class:`~yarl.URL` object are always unquoted, for getting
quoted version please convert URL into :class:`bytes`::

   >>> bytes(url)
   b'https://www.python.org/%7Eguido?arg=1#frag'

Constructing URL from bytes performs unquoting as well::

   >>> URL(b'https://www.python.org/%7Eguido')
   URL('https://www.python.org/~guido')

For full documentation please read :ref:`yarl-api` section.


Installation
------------

::

   $ pip install yarl

The library is Python 3 only!


API documentation
------------------

Open :ref:`yarl-api` for reading full list of available methods.

Source code
-----------

The project is hosted on GitHub_

Please file an issue on the `bug tracker
<https://github.com/aio-libs/yarl/issues>`_ if you have found a bug
or have some suggestion in order to improve the library.

The library uses `Travis <https://travis-ci.org/aio-libs/yarl>`_ for
Continuous Integration.

Discussion list
---------------

*aio-libs* google group: https://groups.google.com/forum/#!forum/aio-libs

Feel free to post your questions and ideas here.


Authors and License
-------------------

The ``yarl`` package is written by Andrew Svetlov.

It's *Apache 2* licensed and freely available.






Contents:

.. toctree::
   :maxdepth: 2

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _GitHub: https://github.com/aio-libs/multidict
