.. _yarl-api:

Public API
==========

.. module:: yarl
.. currentmodule:: yarl


The only public *yarl* class is :class:`URL`:

.. doctest::

   >>> from yarl import URL


.. class:: URL(arg, *, encoded=False)

Represents URL as ::

   [scheme:]//[user[:password]@]host[:port][/path][?query][#fragment]

for absolute URLs and ::

   [/path][?query][#fragment]

for relative
ones (:ref:`yarl-api-relative-urls`).

The URL structure is::

    http://user:pass@example.com:8042/over/there?name=ferret#nose
    \__/   \__/ \__/ \_________/ \__/\_________/ \_________/ \__/
     |      |    |        |       |      |           |        |
   scheme  user password host    port   path       query   fragment


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

   >>> str(URL('http://εμπορικόσήμα.eu/шлях/這裡'))
   'http://xn--jxagkqfkduily1i.eu/%D1%88%D0%BB%D1%8F%D1%85/%E9%80%99%E8%A3%A1'

The same is true for *user*, *password*, *query* and *fragment* parts of URL.

Already encoded URL is not changed:

.. doctest::

   >>> URL('http://xn--jxagkqfkduily1i.eu')
   URL('http://xn--jxagkqfkduily1i.eu')

Use :meth:`~URL.human_repr` for getting human readable representation:

.. doctest::

   >>> url = URL('http://εμπορικόσήμα.eu/шлях/這裡')
   >>> str(url)
   'http://xn--jxagkqfkduily1i.eu/%D1%88%D0%BB%D1%8F%D1%85/%E9%80%99%E8%A3%A1'
   >>> url.human_repr()
   'http://εμπορικόσήμα.eu/шлях/這裡'


.. note::

   Sometimes encoding performed by *yarl* is not acceptable for
   certain WEB server.

   Passing ``encoded=True`` parameter prevents URL auto-encoding, user is
   responsible about URL correctness.

   Don't use this option unless there is no other way for keeping URL
   attributes not touched.

   Any URL manipulations don't guarantee correct encoding, URL parts
   could be re-quoted even if *encoded* parameter was explicitly set.

URL properties
--------------

There are two kinds of properties: *decoded* and *encoded* (with
``raw_`` prefix):


.. attribute:: URL.scheme

   Scheme for absolute URLs, empty string for relative URLs or URLs
   starting with ``'//'`` (:ref:`yarl-api-relative-urls`).

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
      >>> URL('http://бажан@example.com').user
      'бажан'
      >>> URL('http://example.com').user is None
      True


.. attribute:: URL.raw_user

   Encoded *user* part of URL, ``None`` if *user* is missing.


   .. doctest::

      >>> URL('http://довбуш@example.com').raw_user
      '%D0%B4%D0%BE%D0%B2%D0%B1%D1%83%D1%88'
      >>> URL('http://example.com').raw_user is None
      True


.. attribute:: URL.password

   Decoded *password* part of URL, ``None`` if *user* is missing.

   .. doctest::

      >>> URL('http://john:pass@example.com').password
      'pass'
      >>> URL('http://степан:пароль@example.com').password
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

   Brackets are stripped for IPv6. Host is converted to lowercase,
   address is validated and converted to compressed form.

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
      >>> URL('http://[::1]').raw_host
      '::1'

.. attribute:: URL.host_subcomponent

   :rfc:`3986#section-3.2.2` host subcomponent part of URL, ``None`` for relative URLs
   (:ref:`yarl-api-relative-urls`).

   .. doctest::

      >>> URL('http://хост.домен').host_subcomponent
      'xn--n1agdj.xn--d1acufc'
      >>> URL('http://[::1]').host_subcomponent
      '[::1]'

   .. versionadded:: 1.13

.. attribute:: URL.port

   *port* part of URL, with scheme-based fallback.

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


.. attribute:: URL.explicit_port

   *explicit_port* part of URL, without scheme-based fallback.

   ``None`` for relative URLs (:ref:`yarl-api-relative-urls`) or for
   URLs without explicit port.

   .. doctest::

      >>> URL('http://example.com:8080').explicit_port
      8080
      >>> URL('http://example.com').explicit_port is None
      True
      >>> URL('page.html').explicit_port is None
      True

   .. versionadded:: 1.3

.. attribute:: URL.authority

   Decoded *authority* part of URL, a combination of *user*, *password*, *host*, and
   *port*.

   ``authority = [ user [ ":" password ] "@" ] host [ ":" port ]``.

   *authority* is empty string if all parts are missing.

   .. doctest::

      >>> URL('http://john:pass@example.com:8000').authority
      'john:pass@example.com:8000'

   .. versionadded:: 1.5

.. attribute:: URL.raw_authority

   Encoded *authority* part of URL, a combination of *user*, *password*, *host*, and
   *port*.  empty string if all parts are missing.

   .. doctest::

      >>> URL('http://john:pass@хост.домен:8000').raw_authority
      'john:pass@xn--n1agdj.xn--d1acufc:8000'

   .. versionadded:: 1.5

.. attribute:: URL.path

   Decoded *path* part of URL, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/path/to').path
      '/path/to'
      >>> URL('http://example.com/шлях/сюди').path
      '/шлях/сюди'
      >>> URL('http://example.com').path
      '/'

   .. warning::

      In many situations it is important to distinguish between path separators
      (a literal ``/``) and other forward slashes (a literal ``%2F``). Use
      :attr:`URL.path_safe` for these cases.

.. attribute:: URL.path_safe

   Similar to :attr:`URL.path` except it doesn't decode ``%2F`` or ``%25``.
   This allows to distinguish between path separators (``/``) and encoded
   slashes (``%2F``).

   Note that ``%25`` is also not decoded to avoid issues with double unquoting
   of values. e.g. You can unquote the value with
   ``URL.path_safe.replace("%2F", "/").replace("%25", %")`` to get the same
   result as :meth:`URL.path`. If the ``%25`` was unquoted, it would be
   impossible to tell the difference between ``%2F`` and ``%252F``.

   .. versionadded:: 1.12

.. attribute:: URL.path_qs

   Decoded *path* part of URL and query string, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/path/to?a1=a&a2=b').path_qs
      '/path/to?a1=a&a2=b'


.. attribute:: URL.raw_path_qs

   Encoded *path* part of URL and query string, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/шлях/сюди?ключ=знач').raw_path_qs
      '/%D1%88%D0%BB%D1%8F%D1%85/%D1%81%D1%8E%D0%B4%D0%B8?%D0%BA%D0%BB%D1%8E%D1%87=%D0%B7%D0%BD%D0%B0%D1%87'

   .. versionadded:: 0.15

.. attribute:: URL.raw_path

   Encoded *path* part of URL, ``'/'`` for absolute URLs without *path* part.

   .. doctest::

      >>> URL('http://example.com/шлях/сюди').raw_path
      '/%D1%88%D0%BB%D1%8F%D1%85/%D1%81%D1%8E%D0%B4%D0%B8'


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
      >>> URL('http://example.com/path#якір').fragment
      'якір'
      >>> URL('http://example.com/path').fragment
      ''

.. attribute:: URL.raw_fragment

   Decoded *fragment* part of URL, empty string if *fragment* is missing.

   .. doctest::

      >>> URL('http://example.com/path#якір').raw_fragment
      '%D1%8F%D0%BA%D1%96%D1%80'



For *path* and *query* *yarl* supports additional helpers:


.. attribute:: URL.parts

   A :class:`tuple` containing decoded *path* parts, ``('/',)`` for
   absolute URLs if *path* is missing.

   .. doctest::

      >>> URL('http://example.com/path/to').parts
      ('/', 'path', 'to')
      >>> URL('http://example.com/шлях/сюди').parts
      ('/', 'шлях', 'сюди')
      >>> URL('http://example.com').parts
      ('/',)

.. attribute:: URL.raw_parts

   A :class:`tuple` containing encoded *path* parts, ``('/',)`` for
   absolute URLs if *path* is missing.

   .. doctest::

      >>> URL('http://example.com/шлях/сюди').raw_parts
      ('/', '%D1%88%D0%BB%D1%8F%D1%85', '%D1%81%D1%8E%D0%B4%D0%B8')

.. attribute:: URL.name

   The last part of :attr:`parts`.

   .. doctest::

      >>> URL('http://example.com/path/to').name
      'to'
      >>> URL('http://example.com/шлях/сюди').name
      'сюди'
      >>> URL('http://example.com/path/').name
      ''

.. attribute:: URL.raw_name

   The last part of :attr:`raw_parts`.

   .. doctest::

      >>> URL('http://example.com/шлях/сюди').raw_name
      '%D1%81%D1%8E%D0%B4%D0%B8'

.. attribute:: URL.suffix

   The file extension of :attr:`name`.

   .. doctest::

      >>> URL('http://example.com/path/to.txt').suffix
      '.txt'
      >>> URL('http://example.com/шлях.сюди').suffix
      '.сюди'
      >>> URL('http://example.com/path').suffix
      ''

.. attribute:: URL.raw_suffix

   The file extension of :attr:`raw_name`.

   .. doctest::

      >>> URL('http://example.com/шлях.сюди').raw_suffix
      '.%D1%81%D1%8E%D0%B4%D0%B8'

.. attribute:: URL.suffixes

   A list of :attr:`name`'s file extensions.

   .. doctest::

      >>> URL('http://example.com/path/to.tar.gz').suffixes
      ('.tar', '.gz')
      >>> URL('http://example.com/шлях.тут.ось').suffixes
      ('.тут', '.ось')
      >>> URL('http://example.com/path').suffixes
      ()

.. attribute:: URL.raw_suffixes

   A list of :attr:`raw_name`'s file extensions.

   .. doctest::

      >>> URL('http://example.com/шлях.тут.ось').raw_suffixes
      ('.%D1%82%D1%83%D1%82', '.%D0%BE%D1%81%D1%8C')


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


.. attribute:: URL.absolute

    A check for absolute URLs.

    Return ``True`` for absolute ones (having *scheme* or starting
    with ``'//'``), ``False`` otherwise.

   .. doctest::

      >>> URL('http://example.com').absolute
      True
      >>> URL('//example.com').absolute
      True
      >>> URL('/path/to').absolute
      False
      >>> URL('path').absolute
      False

   .. versionchanged:: 1.9.10

      The :attr:`~yarl.URL.absolute` property is preferred over the ``is_absolute()`` method.


New URL generation
------------------

URL is an immutable object, every operation described in the
section generates a new :class:`URL` instance.

.. method:: URL.build(*, scheme=..., authority=..., user=..., password=..., \
                      host=..., port=..., path=..., query=..., \
                      query_string=..., fragment=..., encoded=False)
   :classmethod:

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

      Only one of ``query`` or ``query_string`` should be passed then ValueError
      will be raised.

.. method:: URL.with_scheme(scheme)

   Return a new URL with *scheme* replaced:

   .. doctest::

      >>> URL('http://example.com').with_scheme('https')
      URL('https://example.com')

   Returned URL may have a *different* ``port``
   (:ref:`default port substitution <yarl-api-default-ports>`).

.. method:: URL.with_user(user)

   Return a new URL with *user* replaced, auto-encode *user* if needed.

   Clear user/password if *user* is ``None``.

   .. doctest::

      >>> URL('http://user:pass@example.com').with_user('new_user')
      URL('http://new_user:pass@example.com')
      >>> URL('http://user:pass@example.com').with_user('олекса')
      URL('http://%D0%BE%D0%BB%D0%B5%D0%BA%D1%81%D0%B0:pass@example.com')
      >>> URL('http://user:pass@example.com').with_user(None)
      URL('http://example.com')

.. method:: URL.with_password(password)

   Return a new URL with *password* replaced, auto-encode *password* if needed.

   Clear password if ``None`` is passed.

   .. doctest::

      >>> URL('http://user:pass@example.com').with_password('пароль')
      URL('http://user:%D0%BF%D0%B0%D1%80%D0%BE%D0%BB%D1%8C@example.com')
      >>> URL('http://user:pass@example.com').with_password(None)
      URL('http://user@example.com')

.. method:: URL.with_host(host)

   Return a new URL with *host* replaced, auto-encode *host* if needed.

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
   auto-encode the argument if needed.

   A sequence of ``(key, value)`` pairs is supported as well.

   Also it can take an arbitrary number of keyword arguments.

   Clear *query* if ``None`` is passed.

   .. note::

      The library accepts :class:`str`, :class:`float`, :class:`int` and their
      subclasses except :class:`bool` as query argument values.

      If a mapping such as :class:`dict` is used, the values may also be
      :class:`list` or :class:`tuple` to represent a key has many values.

      Please see :ref:`yarl-bools-support` for the reason why :class:`bool` is not
      supported out-of-the-box.

   .. doctest::

      >>> URL('http://example.com/path?a=b').with_query('c=d')
      URL('http://example.com/path?c=d')
      >>> URL('http://example.com/path?a=b').with_query({'c': 'd'})
      URL('http://example.com/path?c=d')
      >>> URL('http://example.com/path?a=b').with_query({'c': [1, 2]})
      URL('http://example.com/path?c=1&c=2')
      >>> URL('http://example.com/path?a=b').with_query({'кл': 'зн'})
      URL('http://example.com/path?%D0%BA%D0%BB=%D0%B7%D0%BD')
      >>> URL('http://example.com/path?a=b').with_query(None)
      URL('http://example.com/path')
      >>> URL('http://example.com/path?a=b&b=1').with_query(b='2')
      URL('http://example.com/path?b=2')
      >>> URL('http://example.com/path?a=b&b=1').with_query([('b', '2')])
      URL('http://example.com/path?b=2')

   .. versionchanged:: 1.5

      Support :class:`list` and :class:`tuple` as a query parameter value.

   .. versionchanged:: 1.6

      Support subclasses of :class:`int` (except :class:`bool`) and :class:`float`
      as a query parameter value.

.. method:: URL.extend_query(query)
            URL.extend_query(**kwargs)

   Returns a new URL with *query* part extended.

   Unlike :meth:`update_query`, this method keeps duplicate keys.

   Returned :class:`URL` object will contain query string which extends
   parts from passed query parts (or parts of parsed query string).

   Accepts any :class:`~collections.abc.Mapping` (e.g. :class:`dict`,
   :class:`~multidict.MultiDict` instances) or :class:`str`,
   auto-encode the argument if needed.

   A sequence of ``(key, value)`` pairs is supported as well.

   Also it can take an arbitrary number of keyword arguments.

   Returns the same :class:`URL` if *query* of ``None`` is passed.

   .. note::

      The library accepts :class:`str`, :class:`float`, :class:`int` and their
      subclasses except :class:`bool` as query argument values.

      If a mapping such as :class:`dict` is used, the values may also be
      :class:`list` or :class:`tuple` to represent a key has many values.

      Please see :ref:`yarl-bools-support` for the reason why :class:`bool` is not
      supported out-of-the-box.

   .. doctest::

      >>> URL('http://example.com/path?a=b&b=1').extend_query(b='2')
      URL('http://example.com/path?a=b&b=1&b=2')
      >>> URL('http://example.com/path?a=b&b=1').extend_query([('b', '2')])
      URL('http://example.com/path?a=b&b=1&b=2')
      >>> URL('http://example.com/path?a=b&c=e&c=f').extend_query(c='d')
      URL('http://example.com/path?a=b&c=e&c=f&c=d')

   .. versionadded:: 1.11.0

.. method:: URL.update_query(query)
            URL.update_query(**kwargs)

   Returns a new URL with *query* part updated.

   Unlike :meth:`with_query` the method does not replace query
   completely.


   Returned :class:`URL` object will contain query string which updated
   parts from passed query parts (or parts of parsed query string).

   Accepts any :class:`~collections.abc.Mapping` (e.g. :class:`dict`,
   :class:`~multidict.MultiDict` instances) or :class:`str`,
   auto-encode the argument if needed.

   A sequence of ``(key, value)`` pairs is supported as well.

   Also it can take an arbitrary number of keyword arguments.

   Clear *query* if ``None`` is passed.

   Mod operator (``%``) can be used as alternative to the direct call of
   :meth:`URL.update_query`.

   .. note::

      The library accepts :class:`str`, :class:`float`, :class:`int` and their
      subclasses except :class:`bool` as query argument values.

      If a mapping such as :class:`dict` is used, the values may also be
      :class:`list` or :class:`tuple` to represent a key has many values.

      Please see :ref:`yarl-bools-support` for the reason why :class:`bool` is not
      supported out-of-the-box.

   .. doctest::

      >>> URL('http://example.com/path?a=b').update_query('c=d')
      URL('http://example.com/path?a=b&c=d')
      >>> URL('http://example.com/path?a=b').update_query({'c': 'd'})
      URL('http://example.com/path?a=b&c=d')
      >>> URL('http://example.com/path?a=b').update_query({'c': [1, 2]})
      URL('http://example.com/path?a=b&c=1&c=2')
      >>> URL('http://example.com/path?a=b').update_query({'кл': 'зн'})
      URL('http://example.com/path?a=b&%D0%BA%D0%BB=%D0%B7%D0%BD')
      >>> URL('http://example.com/path?a=b&b=1').update_query(b='2')
      URL('http://example.com/path?a=b&b=2')
      >>> URL('http://example.com/path?a=b&b=1').update_query([('b', '2')])
      URL('http://example.com/path?a=b&b=2')
      >>> URL('http://example.com/path?a=b&c=e&c=f').update_query(c='d')
      URL('http://example.com/path?a=b&c=d')
      >>> URL('http://example.com/path?a=b').update_query('c=d&c=f')
      URL('http://example.com/path?a=b&c=d&c=f')
      >>> URL('http://example.com/path?a=b') % {'c': 'd'}
      URL('http://example.com/path?a=b&c=d')

   .. versionchanged:: 1.0

      All multiple key/value pairs are applied to the multi-dictionary.

   .. versionadded:: 1.5

      Support for mod operator (``%``) to update the URL's query part.

   .. versionchanged:: 1.5

      Support :class:`list` and :class:`tuple` as a query parameter value.

   .. versionchanged:: 1.6

      Support subclasses of :class:`int` (except :class:`bool`) and :class:`float`
      as a query parameter value.

.. method:: URL.without_query_params(*query_params)

   Return a new URL whose *query* part does not contain specified ``query_params``.

   Accepts :class:`str` for ``query_params``.

   It does nothing if none of specified ``query_params`` are present in the query.

   .. versionadded:: 1.10.0

.. method:: URL.with_fragment(fragment)

   Return a new URL with *fragment* replaced, auto-encode *fragment* if needed.

   Clear *fragment* to default if ``None`` is passed.

   .. doctest::

      >>> URL('http://example.com/path#frag').with_fragment('anchor')
      URL('http://example.com/path#anchor')
      >>> URL('http://example.com/path#frag').with_fragment('якір')
      URL('http://example.com/path#%D1%8F%D0%BA%D1%96%D1%80')
      >>> URL('http://example.com/path#frag').with_fragment(None)
      URL('http://example.com/path')

.. method:: URL.with_name(name)

   Return a new URL with *name* (last part of *path*) replaced and
   cleaned up *query* and *fragment* parts.

   Name is encoded if needed.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').with_name('new')
      URL('http://example.com/path/new')
      >>> URL('http://example.com/path/to').with_name("ім'я")
      URL('http://example.com/path/%D1%96%D0%BC%27%D1%8F')

.. method:: URL.with_suffix(suffix)

   Return a new URL with *suffix* (file extension of *name*) replaced and
   cleaned up *query* and *fragment* parts.

   Name is encoded if needed.

   .. doctest::

      >>> URL('http://example.com/path/to?arg#frag').with_suffix('.doc')
      URL('http://example.com/path/to.doc')
      >>> URL('http://example.com/path/to').with_suffix('.cуфікс')
      URL('http://example.com/path/to.c%D1%83%D1%84%D1%96%D0%BA%D1%81')

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
      >>> url = URL('http://example.com/path?arg#frag') / 'сюди'
      >>> url
      URL('http://example.com/path/%D1%81%D1%8E%D0%B4%D0%B8')

.. method:: URL.joinpath(*other, encoded=False)

   Construct a new URL by with all ``other`` elements appended to
   *path*, and cleaned up *query* and *fragment* parts.

   Passing ``encoded=True`` parameter prevents path element auto-encoding, the caller is
   responsible for taking care of URL correctness.

   .. doctest::

      >>> url = URL('http://example.com/path?arg#frag').joinpath('to', 'subpath')
      >>> url
      URL('http://example.com/path/to/subpath')
      >>> url.parts
      ('/', 'path', 'to', 'subpath')
      >>> url = URL('http://example.com/path?arg#frag').joinpath('сюди')
      >>> url
      URL('http://example.com/path/%D1%81%D1%8E%D0%B4%D0%B8')
      >>> url = URL('http://example.com/path').joinpath('%D1%81%D1%8E%D0%B4%D0%B8', encoded=True)
      >>> url
      URL('http://example.com/path/%D1%81%D1%8E%D0%B4%D0%B8')

   .. versionadded:: 1.9

.. method:: URL.__truediv__(url)

   Shortcut for :meth:`URL.joinpath` with a single element and ``encoded=False``.

   .. doctest::

      >>> url = URL('http://example.com/path?arg#frag') / 'to'
      >>> url
      URL('http://example.com/path/to')
      >>> url.parts
      ('/', 'path', 'to')

   .. versionadded:: 0.9

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
      ``scheme://``), the URL‘s host name and/or scheme will be
      present in the result, e.g.:

      .. doctest::

         >>> base = URL('http://example.com/path/index.html')
         >>> base.join(URL('//python.org/page.html'))
         URL('http://python.org/page.html')

Human readable representation
-----------------------------

All URL data is stored in encoded form internally. It's pretty good
for passing ``str(url)`` everywhere URL string is accepted but quite
bad for memorizing by humans.

.. method:: URL.human_repr()

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


Cache control
-------------

IDNA conversion, host validation, and IP Address parsing used for host
encoding are quite expensive operations, that's why the ``yarl``
library caches these calls by storing last ``256`` results in the
global LRU cache.

.. function:: cache_clear()

   Clear IDNA, host validation, and IP Address caches.


.. function:: cache_info()

   Return a dictionary with ``"idna_encode"``, ``"idna_decode"``, ``"ip_address"``,
   and ``"host_validate"`` keys, each value
   points to corresponding ``CacheInfo`` structure (see :func:`functools.lru_cache` for
   details):

   .. doctest::
      :options: +SKIP

      >>> yarl.cache_info()
      {'idna_encode': CacheInfo(hits=5, misses=5, maxsize=256, currsize=5),
       'idna_decode': CacheInfo(hits=24, misses=15, maxsize=256, currsize=15),
       'ip_address': CacheInfo(hits=46933, misses=84, maxsize=256, currsize=101),
       'host_validate': CacheInfo(hits=0, misses=0, maxsize=256, currsize=0)}



.. function:: cache_configure(*, idna_encode_size=256, idna_decode_size=256, ip_address_size=256, host_validate_size=256)

   Set the IP Address, host validation, and IDNA encode and
   decode cache sizes (``256`` for each by default).

   Pass ``None`` to make the corresponding cache unbounded (may speed up host encoding
   operation a little but the memory footprint can be very high,
   please use with caution).

References
----------

:mod:`yarl` stays on shoulders of giants: several RFC documents and
low-level :mod:`urllib.parse` which performs almost all gory work.

The module borrowed design from :mod:`pathlib` in any place where it was
possible.

.. seealso::

   :rfc:`5891` - Internationalized Domain Names in Applications (IDNA): Protocol
      Document describing non-ASCII domain name encoding.

   :rfc:`3987` - Internationalized Resource Identifiers
      This specifies conversion rules for non-ASCII characters in URL.

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
