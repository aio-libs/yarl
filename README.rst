yarl
====

.. image:: https://dev.azure.com/aio-libs/yarl/_apis/build/status/CI?branchName=master
  :target: https://dev.azure.com/aio-libs/yarl/_build/latest?definitionId=7&branchName=master
  :align: right

.. image:: https://codecov.io/gh/aio-libs/yarl/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/aio-libs/yarl

.. image:: https://badge.fury.io/py/yarl.svg
    :target: https://badge.fury.io/py/yarl


.. image:: https://readthedocs.org/projects/yarl/badge/?version=latest
    :target: https://yarl.readthedocs.io


.. image:: https://img.shields.io/pypi/pyversions/yarl.svg
    :target: https://pypi.python.org/pypi/yarl

.. image:: https://badges.gitter.im/Join%20Chat.svg
    :target: https://gitter.im/aio-libs/Lobby
    :alt: Chat on Gitter

Introduction
------------

Url is constructed from ``str``::

   >>> from yarl import URL
   >>> url = URL('https://www.python.org/~guido?arg=1#frag')
   >>> url
   URL('https://www.python.org/~guido?arg=1#frag')

All url parts: *scheme*, *user*, *password*, *host*, *port*, *path*,
*query* and *fragment* are accessible by properties::

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

All url manipulations produce a new url object::

   >>> url.parent / 'downloads/source'
   URL('https://www.python.org/downloads/source')

Strings passed to constructor and modification methods are
automatically encoded giving canonical representation as result::

   >>> url = URL('https://www.python.org/путь')
   >>> url
   URL('https://www.python.org/%D0%BF%D1%83%D1%82%D1%8C')

Regular properties are *percent-decoded*, use ``raw_`` versions for
getting *encoded* strings::

   >>> url.path
   '/путь'

   >>> url.raw_path
   '/%D0%BF%D1%83%D1%82%D1%8C'

Human readable representation of URL is available as ``.human_repr()``::

   >>> url.human_repr()
   'https://www.python.org/путь'

For full documentation please read https://yarl.readthedocs.org.


Installation
------------

::

   $ pip install yarl

The library is Python 3 only!


Dependencies
------------

YARL requires multidict_ library.


API documentation
------------------

The documentation is located at https://yarl.readthedocs.org


Why isn't boolean supported by the URL query API?
-------------------------------------------------

There is no standard for boolean representation of boolean values.

Some systems prefer ``true``/``false``, others like ``yes``/``no``, ``on``/``off``,
``Y``/``N``, ``1``/``0``, etc.

``yarl`` cannot make an unambiguous decision on how to serialize ``bool`` values because
it is specific to how the end-user's application is built and would be different for
different apps.  The library doesn't accept booleans in the API; a user should convert
bools into strings using own preferred translation protocol.


Comparison with other URL libraries
------------------------------------

* furl (https://pypi.python.org/pypi/furl)

  The library has rich functionality but the ``furl`` object is mutable.

  I'm afraid to pass this object into foreign code: who knows if the
  code will modify my url in a terrible way while I just want to send URL
  with handy helpers for accessing URL properties.

  ``furl`` has other non-obvious tricky things but the main objection
  is mutability.

* URLObject (https://pypi.python.org/pypi/URLObject)

  URLObject is immutable, that's pretty good.

  Every URL change generates a new URL object.

  But the library doesn't do any decode/encode transformations leaving the
  end user to cope with these gory details.


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


.. _GitHub: https://github.com/aio-libs/yarl

.. _multidict: https://github.com/aio-libs/multidict
