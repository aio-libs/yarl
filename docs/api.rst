.. _yarl-api:

Public API
==========

.. module:: yarl
.. currentmodule:: yarl


The only public *yarl* class is ``URL``:

.. doctest::

   >>> from yarl import URL


.. class:: URL(arg)

Represents URL as
``[scheme:]//[user:[password]@]host[:port][/path][?query][#fragment]``
for absolute URLs and ``[/path][?query][#fragment]`` for relative
ones (:ref:`yarl-api-relative-urls`).

It accepts either :class:`str` or :class:`bytes` as an argument.

:class:`str` assumes your *arg* is an *decoded* url:

.. doctest::

   >>> url = URL('http://example.com/path/to/?arg1=a&arg2=b#fragment')
   >>> url
   URL('http://example.com/path/to/?arg1=a&arg2=b#fragment')

For giving *encoded* version you need conversion to :class:`bytes`:

.. doctest::

   >>> bytes(url)
   b'http://example.com/path/to/?arg1=a&arg2=b#fragment'

Unless *arg* contains the only *ascii* characters there is no differences.

But for *non-ascii* case *url quoting* and *idna encoding* should be applyed.

.. doctest::

   >>> url = URL('http://εμπορικόσήμα.eu/путь/這裡')
   >>> bytes(url)
   b'http://xn--jxagkqfkduily1i.eu/%D0%BF%D1%83%D1%82%D1%8C/%E9%80%99%E8%A3%A1'

The same is true for *user*, *password*, *query* and *fragment* parts of URL.

The reverse translations are performed when you push :class:`bytes` into URL
constructor:

.. doctest::

   >>> url = URL(b'http://xn--jxagkqfkduily1i.eu/%E9%80%99%E8%A3%A1')
   >>> str(url)
   'http://εμπορικόσήμα.eu/這裡'


URL properties
--------------

You migth to get the following data from :class:`URL` object:

.. doctest::

   >>> url = URL('http://user:pass@example.com:8080/path/to?a1=a&a2=b#frag')

.. attribute:: URL.scheme

   .. doctest::

      >>> url.scheme
      'http'

   ``None`` for relative URLs or URLs starting with `'//'`
   (:ref:`yarl-api-relative-urls`).

.. attribute:: URL.user

   .. doctest::

      >>> url.user
      'user'

   ``None`` if *user* was not set.

.. attribute:: URL.password

   .. doctest::

      >>> url.password
      'pass'

   ``None`` if *password* was not set.


.. attribute:: URL.host

   .. doctest::

      >>> url.host
      'example.com'

   Empty string for relative URLs (:ref:`yarl-api-relative-urls`).


.. attribute:: URL.port

   .. doctest::

      >>> url.port
      8080

   ``None`` for relative URLs or for :attr:`URL.scheme`
   without default port substitution (:ref:`yarl-api-relative-urls`).

   .. seealso::

      :ref:`yarl-api-default-ports`


.. attribute:: URL.path

   .. doctest::

      >>> url.path
      '/path/to'

   The value is empty string if *path* part of URL is not present.


.. attribute:: URL.query_string

   .. doctest::

      >>> url.query_string
      'a1=a&a2=b'

   The value is empty string if *query* part of URL is not present.


.. attribute:: URL.fragment

   .. doctest::

      >>> url.fragment
      'frag'

   The value is empty string if *fragment* part of URL is not present.


For *path* and *query* :mod:`yarl` supports additional helpers:


.. attribute:: URL.parts

   A :class:`tuple` containing *path* parts.

   .. doctest::

      >>> url.parts
      ('/', 'path', 'to')

   If *path* was not set the value is ``('/',)`` for absolute URLs and
   empty tuple ``()`` for relative ones (:ref:`yarl-api-relative-urls`).

.. attribute:: URL.query

   A :class:`multidict.MultiDictProxy` representing parsed *query* parameters.

   .. doctest::

      >>> url.query
      <MultiDictProxy('a1': 'a', 'a2': 'b')>

   Empty value if URL has no *query* part.



.. _yarl-api-relative-urls:

Absolute and relative URLs
--------------------------

:mod:`yarl` supports both absolute an relative URLs.

Absulute URL should start from either *scheme* or ``'//'``.


.. attribute:: URL.is_absolute()

   .. doctest::

      >>> URL('http://example.com').is_absolute()
      True

      >>> URL('//example.com').is_absolute()
      True

      >>> URL('/path/to').is_absolute()
      False

      >>> URL('path').is_absolute()
      False


.. _yarl-api-default-ports:

Default port substitution
-------------------------

:mod:`yarl` is aware about the following *scheme* -> *port* translations:

+------------------+-------+
| scheme           | port  |
+==================+=======+
| ``'http'``       | 80    |
+------------------+-------+
| ``'https'``      | 443   |
+------------------+-------+
| ``'ws'``         | 80    |
+------------------+-------+
| ``'wss'``        | 443   |
+------------------+-------+



References
----------

:mod:`yarl` stays on shoulders of giants: several RFC documents and
low-level :mod:`urllib.parse` which performs almost all gory work.

The module borrowed design from :mod:`pathlib` in any place where it was
possible.

.. seealso::

   :rfc:`3986` - Uniform Resource Identifiers
      This is the current standard (STD66). Any changes to :mod:`yarl` module
      should conform to this. Certain deviations could be observed, which are
      mostly for backward compatibility purposes and for certain de-facto
      parsing requirements as commonly observed in major browsers.

   :rfc:`2732` - Format for Literal IPv6 Addresses in URL's.
      This specifies the parsing requirements of IPv6 URLs.

   :rfc:`2396` - Uniform Resource Identifiers (URI): Generic Syntax
      Document describing the generic syntactic requirements for both
      Uniform Resource Names (URNs) and Uniform Resource Locators
      (URLs).

   :rfc:`2368` - The mailto URL scheme.
      Parsing requirements for mailto URL schemes.

   :rfc:`1808` - Relative Uniform Resource Locators This Request For
      Comments includes the rules for joining an absolute and a
      relative URL, including a fair number of "Abnormal Examples"
      which govern the treatment of border cases.

   :rfc:`1738` - Uniform Resource Locators (URL)
      This specifies the formal syntax and semantics of absolute URLs.
