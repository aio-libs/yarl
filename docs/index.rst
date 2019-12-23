.. yarl documentation master file, created by
   sphinx-quickstart on Mon Aug 29 19:55:36 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

yarl
====

The module provides handy :class:`~yarl.URL` class for URL parsing and
changing.

Introduction
------------

URL is constructed from :class:`str`:

.. doctest::

   >>> from yarl import URL
   >>> url = URL('https://www.python.org/~guido?arg=1#frag')
   >>> url
   URL('https://www.python.org/~guido?arg=1#frag')

All URL parts: *scheme*, *user*, *password*, *host*, *port*, *path*,
*query* and *fragment* are accessible by properties:

.. doctest::

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

All URL manipulations produces a new URL object:

.. doctest::

   >>> url.parent / 'downloads/source'
   URL('https://www.python.org/downloads/source')

Strings passed to constructor and modification methods are
automatically encoded giving canonical representation as result:

.. doctest::

   >>> url = URL('https://www.python.org/путь')
   >>> url
   URL('https://www.python.org/%D0%BF%D1%83%D1%82%D1%8C')

Regular properties are *percent-decoded*, use ``raw_`` versions for
getting *encoded* strings:

.. doctest::

   >>> url.path
   '/путь'

   >>> url.raw_path
   '/%D0%BF%D1%83%D1%82%D1%8C'

Human readable representation of URL is available as :meth:`~yarl.URL.human_repr()`:

.. doctest::

   >>> url.human_repr()
   'https://www.python.org/путь'

For full documentation please read :ref:`yarl-api` section.


Installation
------------

::

   $ pip install yarl

The library is Python 3 only!


Dependencies
------------

YARL requires :mod:`multidict` library.

It installs it automatically.


API documentation
------------------

Open :ref:`yarl-api` for reading full list of available methods.


Comparison with other URL libraries
------------------------------------

* furl (https://pypi.python.org/pypi/furl)

  The library has a rich functionality but ``furl`` object is mutable.

  I afraid to pass this object into foreign code: who knows if the
  code will modify my URL in a terrible way while I just want to send URL
  with handy helpers for accessing URL properties.

  ``furl`` has other non obvious tricky things but the main objection
  is mutability.

* URLObject (https://pypi.python.org/pypi/URLObject)

  URLObject is immutable, that's pretty good.

  Every URL change generates a new URL object.

  But the library doesn't any decode/encode transformations leaving end
  user to cope with these gory details.


.. _yarl-bools-support:

Why isn't boolean supported by the URL query API?
-------------------------------------------------

There is no standard for boolean representation of boolean values.

Some systems prefer ``true``/``false``, others like ``yes``/``no``, ``on``/``off``,
``Y``/``N``, ``1``/``0``, etc.

``yarl`` cannot make an unambiguous decision on how to serialize :class:`bool` values
because it is specific to how the end-user's application is built and would be different
for different apps.  The library doesn't accept booleans in the API; a user should
convert bools into strings using own preferred translation protocol.

Source code
-----------

The project is hosted on GitHub_

Please file an issue on the `bug tracker
<https://github.com/aio-libs/yarl/issues>`_ if you have found a bug
or have some suggestion in order to improve the library.

The library uses `Azure Pipelines <https://dev.azure.com/aio-libs/yarl>`_ for
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


.. _GitHub: https://github.com/aio-libs/yarl
