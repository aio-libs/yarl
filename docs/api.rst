.. _yarl-api:

Public API
==========

.. module:: yarl
.. currentmodule:: yarl


The only public *yarl* class is ``URL``:

.. doctest::

   >>> from yarl import URL


.. class:: URL(arg)

Represents URL as ::

   [scheme:]//[user[:password]@]host[:port][/path][?query][#fragment]

for absolute URLs and ::

   [/path][?query][#fragment]

for relative
ones (:ref:`yarl-api-relative-urls`).

Internally all data are stored as *percent-encoded* strings for
*user*, *path*, *query* and *fragment* and *IDNA-encoded* for *host*
URL parts.

Constructor and midification operators perform *encoding* for all
parts automatically.
The library assumes all data uses *UTF-8* for *percent-encoded* tokens.

.. doctest::

   >>> URL('http://example.com/path/to/?arg1=a&arg2=b#fragment')
   URL('http://example.com/path/to/?arg1=a&arg2=b#fragment')

Unless URL contain the only *ascii* characters there is no differences.

But for *non-ascii* case *encoding* is applyed.

.. doctest::

   >>> url = URL('http://εμπορικόσήμα.eu/путь/這裡')
   >>> str(url)
   'http://xn--jxagkqfkduily1i.eu/%D0%BF%D1%83%D1%82%D1%8C/%E9%80%99%E8%A3%A1'

The same is true for *user*, *password*, *query* and *fragment* parts of URL.

Already encoded URL is not changed:

.. doctest::

   >>> URL('http://xn--jxagkqfkduily1i.eu')
   URL('http://xn--jxagkqfkduily1i.eu')

Use :meth:`URL.human_repr` getting human readable representation:

.. doctest::

   >>> url = URL('http://εμπορικόσήμα.eu/путь/這裡')
   >>> str(url)
   'http://xn--jxagkqfkduily1i.eu/%D0%BF%D1%83%D1%82%D1%8C/%E9%80%99%E8%A3%A1'
   >>> url.human_repr()
   'http://εμπορικόσήμα.eu/путь/這裡'

URL properties
--------------

There are tho kinds of properties: *decoded* and *encoded* (with
``raw_`` prefix):


.. attribute:: URL.scheme

   Scheme for absolute URLs.

   .. doctest::

      >>> url = URL('http://example.com')
      >>> url.scheme
      'http'

   ``None`` for relative URLs or URLs starting with `'//'`
   (:ref:`yarl-api-relative-urls`).

   .. doctest::

      >>> url = URL('page.html')
      >>> url.scheme
      None

.. attribute:: URL.user

   Decoded *user* part of URL.

   .. doctest::

      >>> url = URL('http://john@example.com')
      >>> url.user
      'john'

   .. doctest::

      >>> url = URL('http://андрей@example.com')
      >>> url.user
      'андрей'

   ``None`` if *user* is not set.

   .. doctest::

      >>> url = URL('http://example.com')
      >>> url.user
      None


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


.. attribute:: URL.name

   The last part of :attr:`parts`.

   .. doctest::

      >>> url.name
      'to'

   May be an empty string if *path* is not present.

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

New URL generaion
-----------------

:class:`URL` is an immutable object, every operation described in the
section generates a new *URL* instance.

.. method:: URL.with_scheme(scheme)

   Return a new URL with *scheme* replaced:

   .. doctest::

      >>> URL('http://example.com').with_scheme('https')
      URL('https://example.com')

.. method:: URL.with_user(user)

   Return a new URL with *user* replaced:

   .. doctest::

      >>> URL('http://user:pass@example.com').with_user('new_user')
      URL('http://new_user:pass@example.com')

.. method:: URL.with_password(password)

   Return a new URL with *password* replaced:

   .. doctest::

      >>> URL('http://user:pass@example.com').with_password('new_pass')
      URL('http://user:new_pass@example.com')

.. method:: URL.with_host(host)

   Return a new URL with *host* replaced:

   .. doctest::

      >>> URL('http://example.com').with_host('python.org')
      URL('http://python.org')

.. method:: URL.with_port(port)

   Return a new URL with *port* replaced:

   .. doctest::

      >>> URL('http://example.com:8888').with_port(9999)
      URL('http://example.com:9999')

.. method:: URL.with_name(name)

   Return a new URL with *name* (last part of *path*) replaced and
   cleaned up *query* and *fragment* parts.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').with_name('new')
      URL('http://example.com/path/new')

.. attr:: URL.parent

   A new URL with last part of *path* removed and
   cleaned up *query* and *fragment* parts.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').parent
      URL('http://example.com/path')

Division (``/``) operator creates a new URL with appeded *path* parts
and cleaned up *query* and *fragment* parts.

   .. doctest::

      >>> url = URL('http://example.com/path?arg#frag') / 'to/subpath'
      >>> url
      URL('http://example.com/path/to/subpath')
      >>> url.parts
      ('/', 'path', 'to', 'subpath')

.. method:: join(url)

   Construct a full (“absolute”) URL by combining a “base URL”
   (``self``) with another URL (``url``). Informally, this uses
   components of the base URL, in particular the addressing scheme,
   the network location and (part of) the path, to provide missing
   components in the relative URL, e.g.:

   .. doctest::

      >>> base = URL('http://example.com/path/index.html')
      >>> base.join(URL('page.html'))
      URL('http://example.com/path/page.html')

   .. note::

      If ``url`` is an absolute URL (that is, starting with ``//`` or
      ``scheme://``), the url‘s host name and/or scheme will be
      present in the result, e.g.:

      .. doctest::

         >>> base = URL('http://example.com/path/index.html')
         >>> base.join(URL('//python.org/page.html'))
         URL('http://python.org/page.html')

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
