.. _yarl-api:

Public API
==========

.. module:: yarl
.. currentmodule:: yarl


The only public *yarl* class is ``URL``:

.. doctest::

   >>> from yarl import URL


.. class:: URL(arg, *, encoded=False)

Represents URL as ::

   [scheme:]//[user[:password]@]host[:port][/path][?query][#fragment]

for absolute URLs and ::

   [/path][?query][#fragment]

for relative
ones (:ref:`yarl-api-relative-urls`).

Internally all data are stored as *percent-encoded* strings for
*user*, *path*, *query* and *fragment* URL parts and
*IDNA-encoded* (:rfc:`5891`) for *host*.

Constructor and modification operators perform *encoding* for all
parts automatically.
The library assumes all data uses *UTF-8* for *percent-encoded* tokens.

.. doctest::

   >>> URL('http://example.com/path/to/?arg1=a&arg2=b#fragment')
   URL('http://example.com/path/to/?arg1=a&arg2=b#fragment')

Unless URL contain the only *ascii* characters there is no differences.

But for *non-ascii* case *encoding* is applied.

.. doctest::

   >>> str(URL('http://εμπορικόσήμα.eu/путь/這裡'))
   'http://xn--jxagkqfkduily1i.eu/%D0%BF%D1%83%D1%82%D1%8C/%E9%80%99%E8%A3%A1'

The same is true for *user*, *password*, *query* and *fragment* parts of URL.

Already encoded URL is not changed:

.. doctest::

   >>> URL('http://xn--jxagkqfkduily1i.eu')
   URL('http://xn--jxagkqfkduily1i.eu')

Use :meth:`URL.human_repr` for getting human readable representation:

.. doctest::

   >>> url = URL('http://εμπορικόσήμα.eu/путь/這裡')
   >>> str(url)
   'http://xn--jxagkqfkduily1i.eu/%D0%BF%D1%83%D1%82%D1%8C/%E9%80%99%E8%A3%A1'
   >>> url.human_repr()
   'http://εμπορικόσήμα.eu/путь/這裡'


.. note::

   Sometimes encoding performed by *yarl* is not acceptable for
   certain WEB server.

   Passing ``encoded=True`` parameter prevents URL autoencoding, user is
   responsible about URL correctness.

   Don't use this option unless there is no other way for keeping URL
   attributes not touched.

   Any URL manipulations don't guarantee correct encoding, URL parts
   could be requoted even if *encoded* parameter was explicitly set.

URL properties
--------------

There are two kinds of properties: *decoded* and *encoded* (with
``raw_`` prefix):


.. attribute:: URL.scheme

   Scheme for absolute URLs, empty string for relative URLs or URLs
   starting with `'//'` (:ref:`yarl-api-relative-urls`).

   .. doctest::

      >>> URL('http://example.com').scheme
      'http'
      >>> URL('//example.com').scheme
      ''
      >>> URL('page.html').scheme
      ''

.. attribute:: URL.user

   Decoded *user* part of URL, ``None`` if *user* is missing.

   .. doctest::

      >>> URL('http://john@example.com').user
      'john'
      >>> URL('http://андрей@example.com').user
      'андрей'
      >>> URL('http://example.com').user is None
      True


.. attribute:: URL.raw_user

   Encoded *user* part of URL, ``None`` if *user* is missing.


   .. doctest::

      >>> URL('http://андрей@example.com').raw_user
      '%D0%B0%D0%BD%D0%B4%D1%80%D0%B5%D0%B9'
      >>> URL('http://example.com').raw_user is None
      True


.. attribute:: URL.password

   Decoded *password* part of URL, ``None`` if *user* is missing.

   .. doctest::

      >>> URL('http://john:pass@example.com').password
      'pass'
      >>> URL('http://андрей:пароль@example.com').password
      'пароль'
      >>> URL('http://example.com').password is None
      True


.. attribute:: URL.raw_password

   Encoded *password* part of URL, ``None`` if *user* is missing.

   .. doctest::

      >>> URL('http://user:пароль@example.com').raw_password
      '%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C'


.. attribute:: URL.host

   Encoded *host* part of URL, ``None`` for relative URLs
   (:ref:`yarl-api-relative-urls`).

   Brackets are stripped for IPv6.

   .. doctest::

      >>> URL('http://example.com').host
      'example.com'
      >>> URL('http://хост.домен').host
      'хост.домен'
      >>> URL('page.html').host is None
      True
      >>> URL('http://[::1]').host
      '::1'

.. attribute:: URL.raw_host

   IDNA decoded *host* part of URL, ``None`` for relative URLs
   (:ref:`yarl-api-relative-urls`).

   .. doctest::

      >>> URL('http://хост.домен').raw_host
      'xn--n1agdj.xn--d1acufc'


.. attribute:: URL.port

   *port* part of URL.

   ``None`` for relative URLs (:ref:`yarl-api-relative-urls`) or for
   URLs without explicit port and :attr:`URL.scheme` without
   :ref:`default port substitution <yarl-api-default-ports>`.

   .. doctest::

      >>> URL('http://example.com:8080').port
      8080
      >>> URL('http://example.com').port
      80
      >>> URL('page.html').port is None
      True


.. attribute:: URL.path

   Decoded *path* part of URL, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/path/to').path
      '/path/to'
      >>> URL('http://example.com/путь/сюда').path
      '/путь/сюда'
      >>> URL('http://example.com').path
      '/'


.. attribute:: URL.path_qs

   Decoded *path* part of URL and query string, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/path/to?a1=a&a2=b').path_qs
      '/path/to?a1=a&a2=b'


.. attribute:: URL.raw_path

   Encoded *path* part of URL, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/путь/сюда').raw_path
      '/%D0%BF%D1%83%D1%82%D1%8C/%D1%81%D1%8E%D0%B4%D0%B0'


.. attribute:: URL.query_string

   Decoded *query* part of URL, empty string if *query* is missing.

   .. doctest::

      >>> URL('http://example.com/path?a1=a&a2=b').query_string
      'a1=a&a2=b'
      >>> URL('http://example.com/path?ключ=знач').query_string
      'ключ=знач'
      >>> URL('http://example.com/path').query_string
      ''

.. attribute:: URL.raw_query_string

   Encoded *query* part of URL, empty string if *query* is missing.

   .. doctest::

      >>> URL('http://example.com/path?ключ=знач').raw_query_string
      '%D0%BA%D0%BB%D1%8E%D1%87=%D0%B7%D0%BD%D0%B0%D1%87'


.. attribute:: URL.fragment

   Encoded *fragment* part of URL, empty string if *fragment* is missing.

   .. doctest::

      >>> URL('http://example.com/path#fragment').fragment
      'fragment'
      >>> URL('http://example.com/path#якорь').fragment
      'якорь'
      >>> URL('http://example.com/path').fragment
      ''

.. attribute:: URL.raw_fragment

   Decoded *fragment* part of URL, empty string if *fragment* is missing.

   .. doctest::

      >>> URL('http://example.com/path#якорь').raw_fragment
      '%D1%8F%D0%BA%D0%BE%D1%80%D1%8C'



For *path* and *query* *yarl* supports additional helpers:


.. attribute:: URL.parts

   A :class:`tuple` containing decoded *path* parts, ``('/',)`` for
   absolute URLs if *path* is missing.

   .. doctest::

      >>> URL('http://example.com/path/to').parts
      ('/', 'path', 'to')
      >>> URL('http://example.com/путь/сюда').parts
      ('/', 'путь', 'сюда')
      >>> URL('http://example.com').parts
      ('/',)

.. attribute:: URL.raw_parts

   A :class:`tuple` containing encoded *path* parts, ``('/',)`` for
   absolute URLs if *path* is missing.

   .. doctest::

      >>> URL('http://example.com/путь/сюда').raw_parts
      ('/', '%D0%BF%D1%83%D1%82%D1%8C', '%D1%81%D1%8E%D0%B4%D0%B0')

.. attribute:: URL.name

   The last part of :attr:`parts`.

   .. doctest::

      >>> URL('http://example.com/path/to').name
      'to'
      >>> URL('http://example.com/путь/сюда').name
      'сюда'
      >>> URL('http://example.com/path/').name
      ''

.. attribute:: URL.raw_name

   The last part of :attr:`raw_parts`.

   .. doctest::

      >>> URL('http://example.com/путь/сюда').raw_name
      '%D1%81%D1%8E%D0%B4%D0%B0'


.. attribute:: URL.query

   A :class:`multidict.MultiDictProxy` representing parsed *query*
   parameters in decoded representation.  Empty value if URL has no
   *query* part.

   .. doctest::

      >>> URL('http://example.com/path?a1=a&a2=b').query
      <MultiDictProxy('a1': 'a', 'a2': 'b')>
      >>> URL('http://example.com/path?ключ=знач').query
      <MultiDictProxy('ключ': 'знач')>
      >>> URL('http://example.com/path').query
      <MultiDictProxy()>



.. _yarl-api-relative-urls:

Absolute and relative URLs
--------------------------

The module supports both absolute and relative URLs.

Absolute URL should start from either *scheme* or ``'//'``.


.. method:: URL.is_absolute()

    A check for absolute URLs.

    Return ``True`` for absolute ones (having *scheme* or starting
    with ``//``), ``False`` otherwise.

   .. doctest::

      >>> URL('http://example.com').is_absolute()
      True
      >>> URL('//example.com').is_absolute()
      True
      >>> URL('/path/to').is_absolute()
      False
      >>> URL('path').is_absolute()
      False


New URL generation
------------------

URL is an immutable object, every operation described in the
section generates a new *URL* instance.

.. method:: URL.build(*, scheme, user, password, host, port, path, query, \
                      query_string, fragment, strict=False)

   Creates and returns a new URL:

   .. doctest::

      >>> URL.build(scheme="http", host="example.com")
      URL('http://example.com')

      >>> URL.build(scheme="http", host="example.com", query={"a": "b"})
      URL('http://example.com/?a=b')

      >>> URL.build(scheme="http", host="example.com", query_string="a=b")
      URL('http://example.com/?a=b')

      >>> URL.build()
      URL('')

   Calling ``build`` method without arguments is equal to calling
   ``__init__`` without arguments.

   .. note::
      When ``scheme`` and ``host`` are passed new URL will be “absolute”. If only one of ``scheme`` or ``host`` is
      passed then AssertionError will be raised.

   .. note::
      Only one of ``query`` or ``query_string`` should be passed then AssertionError will be raised.

.. method:: URL.with_scheme(scheme)

   Return a new URL with *scheme* replaced:

   .. doctest::

      >>> URL('http://example.com').with_scheme('https')
      URL('https://example.com')

.. method:: URL.with_user(user)

   Return a new URL with *user* replaced, autoencode *user* if needed.

   Clear user/password if *user* is ``None``.

   .. doctest::

      >>> URL('http://user:pass@example.com').with_user('new_user')
      URL('http://new_user:pass@example.com')
      >>> URL('http://user:pass@example.com').with_user('вася')
      URL('http://%D0%B2%D0%B0%D1%81%D1%8F:pass@example.com')
      >>> URL('http://user:pass@example.com').with_user(None)
      URL('http://example.com')

.. method:: URL.with_password(password)

   Return a new URL with *password* replaced, autoencode *password* if needed.

   Clear password if ``None`` is passed.

   .. doctest::

      >>> URL('http://user:pass@example.com').with_password('пароль')
      URL('http://user:%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C@example.com')
      >>> URL('http://user:pass@example.com').with_password(None)
      URL('http://user@example.com')

.. method:: URL.with_host(host)

   Return a new URL with *host* replaced, autoencode *host* if needed.

   Changing *host* for relative URLs is not allowed, use
   :meth:`URL.join` instead.

   .. doctest::

      >>> URL('http://example.com/path/to').with_host('python.org')
      URL('http://python.org/path/to')
      >>> URL('http://example.com/path').with_host('хост.домен')
      URL('http://xn--n1agdj.xn--d1acufc/path')

.. method:: URL.with_port(port)

   Return a new URL with *port* replaced.

   Clear port to default if ``None`` is passed.

   .. doctest::

      >>> URL('http://example.com:8888').with_port(9999)
      URL('http://example.com:9999')
      >>> URL('http://example.com:8888').with_port(None)
      URL('http://example.com')

.. method:: URL.with_path(path)

   Return a new URL with *path* replaced, encode *path* if needed.

   .. doctest::

      >>> URL('http://example.com/').with_path('/path/to')
      URL('http://example.com/path/to')


.. method:: URL.with_query(query)
            URL.with_query(**kwargs)

   Return a new URL with *query* part replaced.

   Unlike :meth:`update_query` the method replaces all query parameters.

   Accepts any :class:`~collections.abc.Mapping` (e.g. :class:`dict`,
   :class:`~multidict.MultiDict` instances) or :class:`str`,
   autoencode the argument if needed.

   A sequence of ``(key, value)`` pairs is supported as well.

   Also it can take an arbitrary number of keyword arguments.

   Clear *query* if ``None`` is passed.

   .. doctest::

      >>> URL('http://example.com/path?a=b').with_query('c=d')
      URL('http://example.com/path?c=d')
      >>> URL('http://example.com/path?a=b').with_query({'c': 'd'})
      URL('http://example.com/path?c=d')
      >>> URL('http://example.com/path?a=b').with_query({'кл': 'зн'})
      URL('http://example.com/path?%D0%BA%D0%BB=%D0%B7%D0%BD')
      >>> URL('http://example.com/path?a=b').with_query(None)
      URL('http://example.com/path')
      >>> URL('http://example.com/path?a=b&b=1').with_query(b='2')
      URL('http://example.com/path?b=2')
      >>> URL('http://example.com/path?a=b&b=1').with_query([('b', '2')])
      URL('http://example.com/path?b=2')

.. method:: URL.update_query(query)
            URL.update_query(**kwargs)

   Returns a new URL with *query* part updated.

   Unlike :meth:`with_query` the method does not replace query
   completely.


   Returned ``URL`` object will contain query string which updated
   parts from passed query parts (or parts of parsed query string).

   Accepts any :class:`~collections.abc.Mapping` (e.g. :class:`dict`,
   :class:`~multidict.MultiDict` instances) or :class:`str`,
   autoencode the argument if needed.

   A sequence of ``(key, value)`` pairs is supported as well.

   Also it can take an arbitrary number of keyword arguments.

   Clear *query* if ``None`` is passed.

   .. doctest::

      >>> URL('http://example.com/path?a=b').update_query('c=d')
      URL('http://example.com/path?a=b&c=d')
      >>> URL('http://example.com/path?a=b').update_query({'c': 'd'})
      URL('http://example.com/path?a=b&c=d')
      >>> URL('http://example.com/path?a=b').update_query({'кл': 'зн'})
      URL('http://example.com/path?a=b&%D0%BA%D0%BB=%D0%B7%D0%BD')
      >>> URL('http://example.com/path?a=b&b=1').update_query(b='2')
      URL('http://example.com/path?a=b&b=2')
      >>> URL('http://example.com/path?a=b&b=1').update_query([('b', '2')])
      URL('http://example.com/path?a=b&b=2')

   .. note::

      Query string will be updated in a similar way to ``dict.update``. Multiple values will be dropped:

      .. doctest::

         >>> URL('http://example.com/path?a=b&c=e&c=f').update_query(c='d')
         URL('http://example.com/path?a=b&c=d')

      When passing multiple values as an argument, only last value will be applied.

      .. doctest::

         >>> URL('http://example.com/path?a=b').update_query('c=d&c=f')
         URL('http://example.com/path?a=b&c=f')

.. method:: URL.with_fragment(port)

   Return a new URL with *fragment* replaced, autoencode *fragment* if needed.

   Clear *fragment* to default if ``None`` is passed.

   .. doctest::

      >>> URL('http://example.com/path#frag').with_fragment('anchor')
      URL('http://example.com/path#anchor')
      >>> URL('http://example.com/path#frag').with_fragment('якорь')
      URL('http://example.com/path#%D1%8F%D0%BA%D0%BE%D1%80%D1%8C')
      >>> URL('http://example.com/path#frag').with_fragment(None)
      URL('http://example.com/path')

.. method:: URL.with_name(name)

   Return a new URL with *name* (last part of *path*) replaced and
   cleaned up *query* and *fragment* parts.

   Name is encoded if needed.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').with_name('new')
      URL('http://example.com/path/new')
      >>> URL('http://example.com/path/to').with_name('имя')
      URL('http://example.com/path/%D0%B8%D0%BC%D1%8F')

.. attribute:: URL.parent

   A new URL with last part of *path* removed and
   cleaned up *query* and *fragment* parts.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').parent
      URL('http://example.com/path')

.. method:: URL.origin()

   A new URL with *scheme*, *host* and *port* parts only.
   *user*, *password*, *path*, *query* and *fragment* are removed.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').origin()
      URL('http://example.com')
      >>> URL('http://user:pass@example.com/path').origin()
      URL('http://example.com')

.. method:: URL.relative()

   A new *relative* URL with  *path*, *query* and *fragment* parts only.
   *scheme*, *user*, *password*, *host* and *port* are removed.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').relative()
      URL('/path/to?arg#frag')

Division (``/``) operator creates a new URL with appended *path* parts
and cleaned up *query* and *fragment* parts.

The path is encoded if needed.

   .. doctest::

      >>> url = URL('http://example.com/path?arg#frag') / 'to/subpath'
      >>> url
      URL('http://example.com/path/to/subpath')
      >>> url.parts
      ('/', 'path', 'to', 'subpath')
      >>> url = URL('http://example.com/path?arg#frag') / 'сюда'
      >>> url
      URL('http://example.com/path/%D1%81%D1%8E%D0%B4%D0%B0')

.. method:: URL.join(url)

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

Human readable representation
-----------------------------

All URL data is stored in encoded form internally. It's pretty good
for passing ``str(url)`` everywhere url string is accepted but quite
bad for memorizing by humans.

.. method:: human_repr()

   Return decoded human readable string for URL representation.

   .. doctest::

      >>> url = URL('http://εμπορικόσήμα.eu/這裡')
      >>> str(url)
      'http://xn--jxagkqfkduily1i.eu/%E9%80%99%E8%A3%A1'
      >>> url.human_repr()
      'http://εμπορικόσήμα.eu/這裡'

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


.. method:: URL.is_default_port()

    A check for default port.

    Return ``True`` if URL's :attr:`~URL.port` is *default* for used
    :attr:`~URL.scheme`, ``False`` otherwise.

    Relative URLs have no default port.

   .. doctest::

      >>> URL('http://example.com').is_default_port()
      True
      >>> URL('http://example.com:80').is_default_port()
      True
      >>> URL('http://example.com:8080').is_default_port()
      False
      >>> URL('/path/to').is_default_port()
      False



References
----------

:mod:`yarl` stays on shoulders of giants: several RFC documents and
low-level :mod:`urllib.parse` which performs almost all gory work.

The module borrowed design from :mod:`pathlib` in any place where it was
possible.

.. seealso::

   :rfc:`5891` - Internationalized Domain Names in Applications (IDNA): Protocol
      Document describing non-ascii domain name encoding.

   :rfc:`3987` - Internationalized Resource Identifiers
      This specifies conversion rules for non-ascii characters in URL.

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
