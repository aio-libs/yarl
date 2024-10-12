=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "changes".

    WARNING: Don't drop the next directive!

.. towncrier release notes start

1.15.0
======

*(2024-10-11)*


Bug fixes
---------

- Fixed validation with :py:meth:`~yarl.URL.with_scheme` when passed scheme is not lowercase -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1189`.


Features
--------

- Started building ``armv7l`` wheels -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1204`.


Miscellaneous internal changes
------------------------------

- Improved performance of constructing unencoded :class:`~yarl.URL` objects -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1188`.

- Added a cache for parsing hosts to reduce overhead of encoding :class:`~yarl.URL` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1190`.

- Improved performance of constructing query strings from :class:`~collections.abc.Mapping` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1193`.

- Improved performance of converting :class:`~yarl.URL` objects to strings -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1198`.


----


1.14.0
======

*(2024-10-08)*


Packaging updates and notes for downstreams
-------------------------------------------

- Switched to using the :mod:`propcache <propcache.api>` package for property caching
  -- by :user:`bdraco`.

  The :mod:`propcache <propcache.api>` package is derived from the property caching
  code in :mod:`yarl` and has been broken out to avoid maintaining it for multiple
  projects.

  *Related issues and pull requests on GitHub:*
  :issue:`1169`.


Contributor-facing changes
--------------------------

- Started testing with Hypothesis -- by :user:`webknjaz` and :user:`bdraco`.

  Special thanks to :user:`Zac-HD` for helping us get started with this framework.

  *Related issues and pull requests on GitHub:*
  :issue:`860`.


Miscellaneous internal changes
------------------------------

- Improved performance of :py:meth:`~yarl.URL.is_default_port` when no explicit port is set -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1168`.

- Improved performance of converting :class:`~yarl.URL` to a string when no explicit port is set -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1170`.

- Improved performance of the :py:meth:`~yarl.URL.origin` method -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1175`.

- Improved performance of encoding hosts -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1176`.


----


1.13.1
======

*(2024-09-27)*


Miscellaneous internal changes
------------------------------

- Improved performance of calling :py:meth:`~yarl.URL.build` with ``authority`` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1163`.


----


1.13.0
======

*(2024-09-26)*


Bug fixes
---------

- Started rejecting ASCII hostnames with invalid characters. For host strings that
  look like authority strings, the exception message includes advice on what to do
  instead -- by :user:`mjpieters`.

  *Related issues and pull requests on GitHub:*
  :issue:`880`, :issue:`954`.

- Fixed IPv6 addresses missing brackets when the :class:`~yarl.URL` was converted to a string -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1157`, :issue:`1158`.


Features
--------

- Added :attr:`~yarl.URL.host_subcomponent` which returns the :rfc:`3986#section-3.2.2` host subcomponent -- by :user:`bdraco`.

  The only current practical difference between :attr:`~yarl.URL.raw_host` and :attr:`~yarl.URL.host_subcomponent` is that IPv6 addresses are returned bracketed.

  *Related issues and pull requests on GitHub:*
  :issue:`1159`.


----


1.12.1
======

*(2024-09-23)*


No significant changes.


----


1.12.0
======

*(2024-09-23)*


Features
--------

- Added :attr:`~yarl.URL.path_safe` to be able to fetch the path without ``%2F`` and ``%25`` decoded -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1150`.


Removals and backward incompatible breaking changes
---------------------------------------------------

- Restore decoding ``%2F`` (``/``) in ``URL.path`` -- by :user:`bdraco`.

  This change restored the behavior before :issue:`1057`.

  *Related issues and pull requests on GitHub:*
  :issue:`1151`.


Miscellaneous internal changes
------------------------------

- Improved performance of processing paths -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1143`.


----


1.11.1
======

*(2024-09-09)*


Bug fixes
---------

- Allowed scheme replacement for relative URLs if the scheme does not require a host -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`280`, :issue:`1138`.

- Allowed empty host for URL schemes other than the special schemes listed in the WHATWG URL spec -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1136`.


Features
--------

- Loosened restriction on integers as query string values to allow classes that implement ``__int__`` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1139`.


Miscellaneous internal changes
------------------------------

- Improved performance of normalizing paths -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1137`.


----


1.11.0
======

*(2024-09-08)*


Features
--------

- Added :meth:`URL.extend_query() <yarl.URL.extend_query>` method, which can be used to extend parameters without replacing same named keys -- by :user:`bdraco`.

  This method was primarily added to replace the inefficient hand rolled method currently used in ``aiohttp``.

  *Related issues and pull requests on GitHub:*
  :issue:`1128`.


Miscellaneous internal changes
------------------------------

- Improved performance of the Cython ``cached_property`` implementation -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1122`.

- Simplified computing ports by removing unnecessary code -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1123`.

- Improved performance of encoding non IPv6 hosts -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1125`.

- Improved performance of :meth:`URL.build() <yarl.URL.build>` when the path, query string, or fragment is an empty string -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1126`.

- Improved performance of the :meth:`URL.update_query() <yarl.URL.update_query>` method -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1130`.

- Improved performance of processing query string changes when arguments are :class:`str` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1131`.


----


1.10.0
======

*(2024-09-06)*


Bug fixes
---------

- Fixed joining a path when the existing path was empty -- by :user:`bdraco`.

  A regression in :meth:`URL.join() <yarl.URL.join>` was introduced in :issue:`1082`.

  *Related issues and pull requests on GitHub:*
  :issue:`1118`.


Features
--------

- Added :meth:`URL.without_query_params() <yarl.URL.without_query_params>` method, to drop some parameters from query string -- by :user:`hongquan`.

  *Related issues and pull requests on GitHub:*
  :issue:`774`, :issue:`898`, :issue:`1010`.

- The previously protected types ``_SimpleQuery``, ``_QueryVariable``, and ``_Query`` are now available for use externally as ``SimpleQuery``, ``QueryVariable``, and ``Query`` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1050`, :issue:`1113`.


Contributor-facing changes
--------------------------

- Replaced all :class:`~typing.Optional` with :class:`~typing.Union` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1095`.


Miscellaneous internal changes
------------------------------

- Significantly improved performance of parsing the network location -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1112`.

- Added internal types to the cache to prevent future refactoring errors -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1117`.


----


1.9.11
======

*(2024-09-04)*


Bug fixes
---------

- Fixed a :exc:`TypeError` with ``MultiDictProxy`` and Python 3.8 -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1084`, :issue:`1105`, :issue:`1107`.


Miscellaneous internal changes
------------------------------

- Improved performance of encoding hosts -- by :user:`bdraco`.

  Previously, the library would unconditionally try to parse a host as an IP Address. The library now avoids trying to parse a host as an IP Address if the string is not in one of the formats described in :rfc:`3986#section-3.2.2`.

  *Related issues and pull requests on GitHub:*
  :issue:`1104`.


----


1.9.10
======

*(2024-09-04)*


Bug fixes
---------

- :meth:`URL.join() <yarl.URL.join>` has been changed to match
  :rfc:`3986` and align with
  :meth:`/ operation <yarl.URL.__truediv__>` and :meth:`URL.joinpath() <yarl.URL.joinpath>`
  when joining URLs with empty segments.
  Previously :py:func:`urllib.parse.urljoin` was used,
  which has known issues with empty segments
  (`python/cpython#84774 <https://github.com/python/cpython/issues/84774>`_).

  Due to the semantics of :meth:`URL.join() <yarl.URL.join>`, joining an
  URL with scheme requires making it relative, prefixing with ``./``.

  .. code-block:: pycon

     >>> URL("https://web.archive.org/web/").join(URL("./https://github.com/aio-libs/yarl"))
     URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')


  Empty segments are honored in the base as well as the joined part.

  .. code-block:: pycon

     >>> URL("https://web.archive.org/web/https://").join(URL("github.com/aio-libs/yarl"))
     URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')



  -- by :user:`commonism`

  This change initially appeared in 1.9.5 but was reverted in 1.9.6 to resolve a problem with query string handling.

  *Related issues and pull requests on GitHub:*
  :issue:`1039`, :issue:`1082`.


Features
--------

- Added :attr:`~yarl.URL.absolute` which is now preferred over ``URL.is_absolute()`` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1100`.


----


1.9.9
=====

*(2024-09-04)*


Bug fixes
---------

- Added missing type on :attr:`~yarl.URL.port` -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1097`.


----


1.9.8
=====

*(2024-09-03)*


Features
--------

- Covered the :class:`~yarl.URL` object with types -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1084`.

- Cache parsing of IP Addresses when encoding hosts -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1086`.


Contributor-facing changes
--------------------------

- Covered the :class:`~yarl.URL` object with types -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1084`.


Miscellaneous internal changes
------------------------------

- Improved performance of handling ports -- by :user:`bdraco`.

  *Related issues and pull requests on GitHub:*
  :issue:`1081`.


----


1.9.7
=====

*(2024-09-01)*


Removals and backward incompatible breaking changes
---------------------------------------------------

- Removed support :rfc:`3986#section-3.2.3` port normalization when the scheme is not one of ``http``, ``https``, ``wss``, or ``ws`` -- by :user:`bdraco`.

  Support for port normalization was recently added in :issue:`1033` and contained code that would do blocking I/O if the scheme was not one of the four listed above. The code has been removed because this library is intended to be safe for usage with :mod:`asyncio`.

  *Related issues and pull requests on GitHub:*
  :issue:`1076`.


Miscellaneous internal changes
------------------------------

- Improved performance of property caching -- by :user:`bdraco`.

  The ``reify`` implementation from ``aiohttp`` was adapted to replace the internal ``cached_property`` implementation.

  *Related issues and pull requests on GitHub:*
  :issue:`1070`.


----


1.9.6
=====

*(2024-08-30)*


Bug fixes
---------

- Reverted :rfc:`3986` compatible :meth:`URL.join() <yarl.URL.join>` honoring empty segments which was introduced in :issue:`1039`.

  This change introduced a regression handling query string parameters with joined URLs. The change was reverted to maintain compatibility with the previous behavior.

  *Related issues and pull requests on GitHub:*
  :issue:`1067`.


----


1.9.5
=====

*(2024-08-30)*


Bug fixes
---------

- Joining URLs with empty segments has been changed
  to match :rfc:`3986`.

  Previously empty segments would be removed from path,
  breaking use-cases such as

  .. code-block:: python

     URL("https://web.archive.org/web/") / "https://github.com/"

  Now :meth:`/ operation <yarl.URL.__truediv__>` and :meth:`URL.joinpath() <yarl.URL.joinpath>`
  keep empty segments, but do not introduce new empty segments.
  e.g.

  .. code-block:: python

     URL("https://example.org/") / ""

  does not introduce an empty segment.

  -- by :user:`commonism` and :user:`youtux`

  *Related issues and pull requests on GitHub:*
  :issue:`1026`.

- The default protocol ports of well-known URI schemes are now taken into account
  during the normalization of the URL string representation in accordance with
  :rfc:`3986#section-3.2.3`.

  Specified ports are removed from the :class:`str` representation of a :class:`~yarl.URL`
  if the port matches the scheme's default port -- by :user:`commonism`.

  *Related issues and pull requests on GitHub:*
  :issue:`1033`.

- :meth:`URL.join() <yarl.URL.join>` has been changed to match
  :rfc:`3986` and align with
  :meth:`/ operation <yarl.URL.__truediv__>` and :meth:`URL.joinpath() <yarl.URL.joinpath>`
  when joining URLs with empty segments.
  Previously :py:func:`urllib.parse.urljoin` was used,
  which has known issues with empty segments
  (`python/cpython#84774 <https://github.com/python/cpython/issues/84774>`_).

  Due to the semantics of :meth:`URL.join() <yarl.URL.join>`, joining an
  URL with scheme requires making it relative, prefixing with ``./``.

  .. code-block:: pycon

     >>> URL("https://web.archive.org/web/").join(URL("./https://github.com/aio-libs/yarl"))
     URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')


  Empty segments are honored in the base as well as the joined part.

  .. code-block:: pycon

     >>> URL("https://web.archive.org/web/https://").join(URL("github.com/aio-libs/yarl"))
     URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')



  -- by :user:`commonism`

  *Related issues and pull requests on GitHub:*
  :issue:`1039`.


Removals and backward incompatible breaking changes
---------------------------------------------------

- Stopped decoding ``%2F`` (``/``) in ``URL.path``, as this could lead to code incorrectly treating it as a path separator
  -- by :user:`Dreamsorcerer`.

  *Related issues and pull requests on GitHub:*
  :issue:`1057`.

- Dropped support for Python 3.7 -- by :user:`Dreamsorcerer`.

  *Related issues and pull requests on GitHub:*
  :issue:`1016`.


Improved documentation
----------------------

- On the :doc:`Contributing docs <contributing/guidelines>` page,
  a link to the ``Towncrier philosophy`` has been fixed.

  *Related issues and pull requests on GitHub:*
  :issue:`981`.

- The pre-existing :meth:`/ magic method <yarl.URL.__truediv__>`
  has been documented in the API reference -- by :user:`commonism`.

  *Related issues and pull requests on GitHub:*
  :issue:`1026`.


Packaging updates and notes for downstreams
-------------------------------------------

- A flaw in the logic for copying the project directory into a
  temporary folder that led to infinite recursion when :envvar:`TMPDIR`
  was set to a project subdirectory path. This was happening in Fedora
  and its downstream due to the use of `pyproject-rpm-macros
  <https://src.fedoraproject.org/rpms/pyproject-rpm-macros>`__. It was
  only reproducible with ``pip wheel`` and was not affecting the
  ``pyproject-build`` users.

  -- by :user:`hroncok` and :user:`webknjaz`

  *Related issues and pull requests on GitHub:*
  :issue:`992`, :issue:`1014`.

- Support Python 3.13 and publish non-free-threaded wheels

  *Related issues and pull requests on GitHub:*
  :issue:`1054`.


Contributor-facing changes
--------------------------

- The CI/CD setup has been updated to test ``arm64`` wheels
  under macOS 14, except for Python 3.7 that is unsupported
  in that environment -- by :user:`webknjaz`.

  *Related issues and pull requests on GitHub:*
  :issue:`1015`.

- Removed unused type ignores and casts -- by :user:`hauntsaninja`.

  *Related issues and pull requests on GitHub:*
  :issue:`1031`.


Miscellaneous internal changes
------------------------------

- ``port``, ``scheme``, and ``raw_host`` are now ``cached_property`` -- by :user:`bdraco`.

  ``aiohttp`` accesses these properties quite often, which cause :mod:`urllib` to build the ``_hostinfo`` property every time. ``port``, ``scheme``, and ``raw_host`` are now cached properties, which will improve performance.

  *Related issues and pull requests on GitHub:*
  :issue:`1044`, :issue:`1058`.


----


1.9.4 (2023-12-06)
==================

Bug fixes
---------

- Started raising :py:exc:`TypeError` when a string value is passed into
  :py:meth:`~yarl.URL.build` as the ``port`` argument  -- by :user:`commonism`.

  Previously the empty string as port would create malformed URLs when rendered as string representations. (:issue:`883`)


Packaging updates and notes for downstreams
-------------------------------------------

- The leading ``--`` has been dropped from the :pep:`517` in-tree build
  backend config setting names. ``--pure-python`` is now just ``pure-python``
  -- by :user:`webknjaz`.

  The usage now looks as follows:

  .. code-block:: console

      $ python -m build \
          --config-setting=pure-python=true \
          --config-setting=with-cython-tracing=true

  (:issue:`963`)


Contributor-facing changes
--------------------------

- A step-by-step :doc:`Release Guide <contributing/release_guide>` guide has
  been added, describing how to release *yarl* -- by :user:`webknjaz`.

  This is primarily targeting maintainers. (:issue:`960`)
- Coverage collection has been implemented for the Cython modules
  -- by :user:`webknjaz`.

  It will also be reported to Codecov from any non-release CI jobs.

  To measure coverage in a development environment, *yarl* can be
  installed in editable mode:

  .. code-block:: console

      $ python -Im pip install -e .

  Editable install produces C-files required for the Cython coverage
  plugin to map the measurements back to the PYX-files.

  :issue:`961`

- It is now possible to request line tracing in Cython builds using the
  ``with-cython-tracing`` :pep:`517` config setting
  -- :user:`webknjaz`.

  This can be used in CI and development environment to measure coverage
  on Cython modules, but is not normally useful to the end-users or
  downstream packagers.

  Here's a usage example:

  .. code-block:: console

      $ python -Im pip install . --config-settings=with-cython-tracing=true

  For editable installs, this setting is on by default. Otherwise, it's
  off unless requested explicitly.

  The following produces C-files required for the Cython coverage
  plugin to map the measurements back to the PYX-files:

  .. code-block:: console

      $ python -Im pip install -e .

  Alternatively, the ``YARL_CYTHON_TRACING=1`` environment variable
  can be set to do the same as the :pep:`517` config setting.

  :issue:`962`


1.9.3 (2023-11-20)
==================

Bug fixes
---------

- Stopped dropping trailing slashes in :py:meth:`~yarl.URL.joinpath` -- by :user:`gmacon`. (:issue:`862`, :issue:`866`)
- Started accepting string subclasses in :meth:`~yarl.URL.__truediv__` operations (``URL / segment``) -- by :user:`mjpieters`. (:issue:`871`, :issue:`884`)
- Fixed the human representation of URLs with square brackets in usernames and passwords -- by :user:`mjpieters`. (:issue:`876`, :issue:`882`)
- Updated type hints to include ``URL.missing_port()``, ``URL.__bytes__()``
  and the ``encoding`` argument to :py:meth:`~yarl.URL.joinpath`
  -- by :user:`mjpieters`. (:issue:`891`)


Packaging updates and notes for downstreams
-------------------------------------------

- Integrated Cython 3 to enable building *yarl* under Python 3.12 -- by :user:`mjpieters`. (:issue:`829`, :issue:`881`)
- Declared modern ``setuptools.build_meta`` as the :pep:`517` build
  backend in :file:`pyproject.toml` explicitly -- by :user:`webknjaz`. (:issue:`886`)
- Converted most of the packaging setup into a declarative :file:`setup.cfg`
  config -- by :user:`webknjaz`. (:issue:`890`)
- The packaging is replaced from an old-fashioned :file:`setup.py` to an
  in-tree :pep:`517` build backend -- by :user:`webknjaz`.

  Whenever the end-users or downstream packagers need to build ``yarl`` from
  source (a Git checkout or an sdist), they may pass a ``config_settings``
  flag ``--pure-python``. If this flag is not set, a C-extension will be built
  and included into the distribution.

  Here is how this can be done with ``pip``:

  .. code-block:: console

      $ python -m pip install . --config-settings=--pure-python=false

  This will also work with ``-e | --editable``.

  The same can be achieved via ``pypa/build``:

  .. code-block:: console

      $ python -m build --config-setting=--pure-python=false

  Adding ``-w | --wheel`` can force ``pypa/build`` produce a wheel from source
  directly, as opposed to building an ``sdist`` and then building from it. (:issue:`893`)

  .. attention::

     v1.9.3 was the only version using the ``--pure-python`` setting name.
     Later versions dropped the ``--`` prefix, making it just ``pure-python``.

- Declared Python 3.12 supported officially in the distribution package metadata
  -- by :user:`edgarrmondragon`. (:issue:`942`)


Contributor-facing changes
--------------------------

- A regression test for no-host URLs was added per :issue:`821`
  and :rfc:`3986` -- by :user:`kenballus`. (:issue:`821`, :issue:`822`)
- Started testing *yarl* against Python 3.12 in CI -- by :user:`mjpieters`. (:issue:`881`)
- All Python 3.12 jobs are now marked as required to pass in CI
  -- by :user:`edgarrmondragon`. (:issue:`942`)
- MyST is now integrated in Sphinx -- by :user:`webknjaz`.

  This allows the contributors to author new documents in Markdown
  when they have difficulties with going straight RST. (:issue:`953`)


1.9.2 (2023-04-25)
==================

Bugfixes
--------

- Fix regression with :meth:`~yarl.URL.__truediv__` and absolute URLs with empty paths causing the raw path to lack the leading ``/``.
  (`#854 <https://github.com/aio-libs/yarl/issues/854>`_)


1.9.1 (2023-04-21)
==================

Bugfixes
--------

- Marked tests that fail on older Python patch releases (< 3.7.10, < 3.8.8 and < 3.9.2) as expected to fail due to missing a security fix for CVE-2021-23336. (`#850 <https://github.com/aio-libs/yarl/issues/850>`_)


1.9.0 (2023-04-19)
==================

This release was never published to PyPI, due to issues with the build process.

Features
--------

- Added ``URL.joinpath(*elements)``, to create a new URL appending multiple path elements. (`#704 <https://github.com/aio-libs/yarl/issues/704>`_)
- Made :meth:`URL.__truediv__() <yarl.URL.__truediv__>` return ``NotImplemented`` if called with an
  unsupported type — by :user:`michaeljpeters`.
  (`#832 <https://github.com/aio-libs/yarl/issues/832>`_)


Bugfixes
--------

- Path normalization for absolute URLs no longer raises a ValueError exception
  when ``..`` segments would otherwise go beyond the URL path root.
  (`#536 <https://github.com/aio-libs/yarl/issues/536>`_)
- Fixed an issue with update_query() not getting rid of the query when argument is None. (`#792 <https://github.com/aio-libs/yarl/issues/792>`_)
- Added some input restrictions on with_port() function to prevent invalid boolean inputs or out of valid port inputs; handled incorrect 0 port representation. (`#793 <https://github.com/aio-libs/yarl/issues/793>`_)
- Made :py:meth:`~yarl.URL.build` raise a :py:exc:`TypeError` if the ``host`` argument is :py:data:`None` — by :user:`paulpapacz`. (`#808 <https://github.com/aio-libs/yarl/issues/808>`_)
- Fixed an issue with ``update_query()`` getting rid of the query when the argument
  is empty but not ``None``. (`#845 <https://github.com/aio-libs/yarl/issues/845>`_)


Misc
----

- `#220 <https://github.com/aio-libs/yarl/issues/220>`_


1.8.2 (2022-12-03)
==================

This is the first release that started shipping wheels for Python 3.11.


1.8.1 (2022-08-01)
==================

Misc
----

- `#694 <https://github.com/aio-libs/yarl/issues/694>`_, `#699 <https://github.com/aio-libs/yarl/issues/699>`_, `#700 <https://github.com/aio-libs/yarl/issues/700>`_, `#701 <https://github.com/aio-libs/yarl/issues/701>`_, `#702 <https://github.com/aio-libs/yarl/issues/702>`_, `#703 <https://github.com/aio-libs/yarl/issues/703>`_, `#739 <https://github.com/aio-libs/yarl/issues/739>`_


1.8.0 (2022-08-01)
==================

Features
--------

- Added ``URL.raw_suffix``, ``URL.suffix``, ``URL.raw_suffixes``, ``URL.suffixes``, ``URL.with_suffix``. (`#613 <https://github.com/aio-libs/yarl/issues/613>`_)


Improved Documentation
----------------------

- Fixed broken internal references to :meth:`~yarl.URL.human_repr`.
  (`#665 <https://github.com/aio-libs/yarl/issues/665>`_)
- Fixed broken external references to :doc:`multidict:index` docs. (`#665 <https://github.com/aio-libs/yarl/issues/665>`_)


Deprecations and Removals
-------------------------

- Dropped Python 3.6 support. (`#672 <https://github.com/aio-libs/yarl/issues/672>`_)


Misc
----

- `#646 <https://github.com/aio-libs/yarl/issues/646>`_, `#699 <https://github.com/aio-libs/yarl/issues/699>`_, `#701 <https://github.com/aio-libs/yarl/issues/701>`_


1.7.2 (2021-11-01)
==================

Bugfixes
--------

- Changed call in ``with_port()`` to stop reencoding parts of the URL that were already encoded. (`#623 <https://github.com/aio-libs/yarl/issues/623>`_)


1.7.1 (2021-10-07)
==================

Bugfixes
--------

- Fix 1.7.0 build error

1.7.0 (2021-10-06)
==================

Features
--------

- Add ``__bytes__()`` magic method so that ``bytes(url)`` will work and use optimal ASCII encoding.
  (`#582 <https://github.com/aio-libs/yarl/issues/582>`_)
- Started shipping platform-specific arm64 wheels for Apple Silicon. (`#622 <https://github.com/aio-libs/yarl/issues/622>`_)
- Started shipping platform-specific wheels with the ``musl`` tag targeting typical Alpine Linux runtimes. (`#622 <https://github.com/aio-libs/yarl/issues/622>`_)
- Added support for Python 3.10. (`#622 <https://github.com/aio-libs/yarl/issues/622>`_)


1.6.3 (2020-11-14)
==================

Bugfixes
--------

- No longer loose characters when decoding incorrect percent-sequences (like ``%e2%82%f8``). All non-decodable percent-sequences are now preserved.
  `#517 <https://github.com/aio-libs/yarl/issues/517>`_
- Provide x86 Windows wheels.
  `#535 <https://github.com/aio-libs/yarl/issues/535>`_


----


1.6.2 (2020-10-12)
==================


Bugfixes
--------

- Provide generated ``.c`` files in TarBall distribution.
  `#530  <https://github.com/aio-libs/multidict/issues/530>`_

1.6.1 (2020-10-12)
==================

Features
--------

- Provide wheels for ``aarch64``, ``i686``, ``ppc64le``, ``s390x`` architectures on
  Linux as well as ``x86_64``.
  `#507  <https://github.com/aio-libs/yarl/issues/507>`_
- Provide wheels for Python 3.9.
  `#526 <https://github.com/aio-libs/yarl/issues/526>`_

Bugfixes
--------

- ``human_repr()`` now always produces valid representation equivalent to the original URL (if the original URL is valid).
  `#511 <https://github.com/aio-libs/yarl/issues/511>`_
- Fixed  requoting a single percent followed by a percent-encoded character in the Cython implementation.
  `#514 <https://github.com/aio-libs/yarl/issues/514>`_
- Fix ValueError when decoding ``%`` which is not followed by two hexadecimal digits.
  `#516 <https://github.com/aio-libs/yarl/issues/516>`_
- Fix decoding ``%`` followed by a space and hexadecimal digit.
  `#520 <https://github.com/aio-libs/yarl/issues/520>`_
- Fix annotation of ``with_query()``/``update_query()`` methods for ``key=[val1, val2]`` case.
  `#528 <https://github.com/aio-libs/yarl/issues/528>`_

Removal
-------

- Drop Python 3.5 support; Python 3.6 is the minimal supported Python version.


----


1.6.0 (2020-09-23)
==================

Features
--------

- Allow for int and float subclasses in query, while still denying bool.
  `#492 <https://github.com/aio-libs/yarl/issues/492>`_


Bugfixes
--------

- Do not requote arguments in ``URL.build()``, ``with_xxx()`` and in ``/`` operator.
  `#502 <https://github.com/aio-libs/yarl/issues/502>`_
- Keep IPv6 brackets in ``origin()``.
  `#504 <https://github.com/aio-libs/yarl/issues/504>`_


----


1.5.1 (2020-08-01)
==================

Bugfixes
--------

- Fix including relocated internal ``yarl._quoting_c`` C-extension into published PyPI dists.
  `#485 <https://github.com/aio-libs/yarl/issues/485>`_


Misc
----

- `#484 <https://github.com/aio-libs/yarl/issues/484>`_


----


1.5.0 (2020-07-26)
==================

Features
--------

- Convert host to lowercase on URL building.
  `#386 <https://github.com/aio-libs/yarl/issues/386>`_
- Allow using ``mod`` operator (``%``) for updating query string (an alias for ``update_query()`` method).
  `#435 <https://github.com/aio-libs/yarl/issues/435>`_
- Allow use of sequences such as ``list`` and ``tuple`` in the values
  of a mapping such as ``dict`` to represent that a key has many values::

      url = URL("http://example.com")
      assert url.with_query({"a": [1, 2]}) == URL("http://example.com/?a=1&a=2")

  `#443 <https://github.com/aio-libs/yarl/issues/443>`_
- Support ``URL.build()`` with scheme and path (creates a relative URL).
  `#464 <https://github.com/aio-libs/yarl/issues/464>`_
- Cache slow IDNA encode/decode calls.
  `#476 <https://github.com/aio-libs/yarl/issues/476>`_
- Add ``@final`` / ``Final`` type hints
  `#477 <https://github.com/aio-libs/yarl/issues/477>`_
- Support URL authority/raw_authority properties and authority argument of ``URL.build()`` method.
  `#478 <https://github.com/aio-libs/yarl/issues/478>`_
- Hide the library implementation details, make the exposed public list very clean.
  `#483 <https://github.com/aio-libs/yarl/issues/483>`_


Bugfixes
--------

- Fix tests with newer Python (3.7.6, 3.8.1 and 3.9.0+).
  `#409 <https://github.com/aio-libs/yarl/issues/409>`_
- Fix a bug where query component, passed in a form of mapping or sequence, is unquoted in unexpected way.
  `#426 <https://github.com/aio-libs/yarl/issues/426>`_
- Hide ``Query`` and ``QueryVariable`` type aliases in ``__init__.pyi``, now they are prefixed with underscore.
  `#431 <https://github.com/aio-libs/yarl/issues/431>`_
- Keep IPv6 brackets after updating port/user/password.
  `#451 <https://github.com/aio-libs/yarl/issues/451>`_


----


1.4.2 (2019-12-05)
==================

Features
--------

- Workaround for missing ``str.isascii()`` in Python 3.6
  `#389 <https://github.com/aio-libs/yarl/issues/389>`_


----


1.4.1 (2019-11-29)
==================

* Fix regression, make the library work on Python 3.5 and 3.6 again.

1.4.0 (2019-11-29)
==================

* Distinguish an empty password in URL from a password not provided at all (#262)

* Fixed annotations for optional parameters of ``URL.build`` (#309)

* Use None as default value of ``user`` parameter of ``URL.build`` (#309)

* Enforce building C Accelerated modules when installing from source tarball, use
  ``YARL_NO_EXTENSIONS`` environment variable for falling back to (slower) Pure Python
  implementation (#329)

* Drop Python 3.5 support

* Fix quoting of plus in path by pure python version (#339)

* Don't create a new URL if fragment is unchanged (#292)

* Included in error message the path that produces starting slash forbidden error (#376)

* Skip slow IDNA encoding for ASCII-only strings (#387)


1.3.0 (2018-12-11)
==================

* Fix annotations for ``query`` parameter (#207)

* An incoming query sequence can have int variables (the same as for
  Mapping type) (#208)

* Add ``URL.explicit_port`` property (#218)

* Give a friendlier error when port can't be converted to int (#168)

* ``bool(URL())`` now returns ``False`` (#272)

1.2.6 (2018-06-14)
==================

* Drop Python 3.4 trove classifier (#205)

1.2.5 (2018-05-23)
==================

* Fix annotations for ``build`` (#199)

1.2.4 (2018-05-08)
==================

* Fix annotations for ``cached_property`` (#195)

1.2.3 (2018-05-03)
==================

* Accept ``str`` subclasses in ``URL`` constructor (#190)

1.2.2 (2018-05-01)
==================

* Fix build

1.2.1 (2018-04-30)
==================

* Pin minimal required Python to 3.5.3 (#189)

1.2.0 (2018-04-30)
==================

* Forbid inheritance, replace ``__init__`` with ``__new__`` (#171)

* Support PEP-561 (provide type hinting marker) (#182)

1.1.1 (2018-02-17)
==================

* Fix performance regression: don't encode empty ``netloc`` (#170)

1.1.0 (2018-01-21)
==================

* Make pure Python quoter consistent with Cython version (#162)

1.0.0 (2018-01-15)
==================

* Use fast path if quoted string does not need requoting (#154)

* Speed up quoting/unquoting by ``_Quoter`` and ``_Unquoter`` classes (#155)

* Drop ``yarl.quote`` and ``yarl.unquote`` public functions (#155)

* Add custom string writer, reuse static buffer if available (#157)
  Code is 50-80 times faster than Pure Python version (was 4-5 times faster)

* Don't recode IP zone (#144)

* Support ``encoded=True`` in ``yarl.URL.build()`` (#158)

* Fix updating query with multiple keys (#160)

0.18.0 (2018-01-10)
===================

* Fallback to IDNA 2003 if domain name is not IDNA 2008 compatible (#152)

0.17.0 (2017-12-30)
===================

* Use IDNA 2008 for domain name processing (#149)

0.16.0 (2017-12-07)
===================

* Fix raising ``TypeError`` by ``url.query_string()`` after
  ``url.with_query({})`` (empty mapping) (#141)

0.15.0 (2017-11-23)
===================

* Add ``raw_path_qs`` attribute (#137)

0.14.2 (2017-11-14)
===================

* Restore ``strict`` parameter as no-op in ``quote`` / ``unquote``

0.14.1 (2017-11-13)
===================

* Restore ``strict`` parameter as no-op for sake of compatibility with
  aiohttp 2.2

0.14.0 (2017-11-11)
===================

* Drop strict mode (#123)

* Fix ``"ValueError: Unallowed PCT %"`` when there's a ``"%"`` in the URL (#124)

0.13.0 (2017-10-01)
===================

* Document ``encoded`` parameter (#102)

* Support relative URLs like ``'?key=value'`` (#100)

* Unsafe encoding for QS fixed. Encode ``;`` character in value parameter (#104)

* Process passwords without user names (#95)

0.12.0 (2017-06-26)
===================

* Properly support paths without leading slash in ``URL.with_path()`` (#90)

* Enable type annotation checks

0.11.0 (2017-06-26)
===================

* Normalize path (#86)

* Clear query and fragment parts in ``.with_path()`` (#85)

0.10.3 (2017-06-13)
===================

* Prevent double URL arguments unquoting (#83)

0.10.2 (2017-05-05)
===================

* Unexpected hash behavior (#75)


0.10.1 (2017-05-03)
===================

* Unexpected compare behavior (#73)

* Do not quote or unquote + if not a query string. (#74)


0.10.0 (2017-03-14)
===================

* Added ``URL.build`` class method (#58)

* Added ``path_qs`` attribute (#42)


0.9.8 (2017-02-16)
==================

* Do not quote ``:`` in path


0.9.7 (2017-02-16)
==================

* Load from pickle without _cache (#56)

* Percent-encoded pluses in path variables become spaces (#59)


0.9.6 (2017-02-15)
==================

* Revert backward incompatible change (BaseURL)


0.9.5 (2017-02-14)
==================

* Fix BaseURL rich comparison support


0.9.4 (2017-02-14)
==================

* Use BaseURL


0.9.3 (2017-02-14)
==================

* Added BaseURL


0.9.2 (2017-02-08)
==================

* Remove debug print


0.9.1 (2017-02-07)
==================

* Do not lose tail chars (#45)


0.9.0 (2017-02-07)
==================

* Allow to quote ``%`` in non strict mode (#21)

* Incorrect parsing of query parameters with %3B (;) inside (#34)

* Fix core dumps (#41)

* ``tmpbuf`` - compiling error (#43)

* Added ``URL.update_path()`` method

* Added ``URL.update_query()`` method (#47)


0.8.1 (2016-12-03)
==================

* Fix broken aiohttp: revert back ``quote`` / ``unquote``.


0.8.0 (2016-12-03)
==================

* Support more verbose error messages in ``.with_query()`` (#24)

* Don't percent-encode ``@`` and ``:`` in path (#32)

* Don't expose ``yarl.quote`` and ``yarl.unquote``, these functions are
  part of private API

0.7.1 (2016-11-18)
==================

* Accept not only ``str`` but all classes inherited from ``str`` also (#25)

0.7.0 (2016-11-07)
==================

* Accept ``int`` as value for ``.with_query()``

0.6.0 (2016-11-07)
==================

* Explicitly use UTF8 encoding in :file:`setup.py` (#20)
* Properly unquote non-UTF8 strings (#19)

0.5.3 (2016-11-02)
==================

* Don't use :py:class:`typing.NamedTuple` fields but indexes on URL construction

0.5.2 (2016-11-02)
==================

* Inline ``_encode`` class method

0.5.1 (2016-11-02)
==================

* Make URL construction faster by removing extra classmethod calls

0.5.0 (2016-11-02)
==================

* Add Cython optimization for quoting/unquoting
* Provide binary wheels

0.4.3 (2016-09-29)
==================

* Fix typing stubs

0.4.2 (2016-09-29)
==================

* Expose ``quote()`` and ``unquote()`` as public API

0.4.1 (2016-09-28)
==================

* Support empty values in query (``'/path?arg'``)

0.4.0 (2016-09-27)
==================

* Introduce ``relative()`` (#16)

0.3.2 (2016-09-27)
==================

* Typo fixes #15

0.3.1 (2016-09-26)
==================

* Support sequence of pairs as ``with_query()`` parameter

0.3.0 (2016-09-26)
==================

* Introduce ``is_default_port()``

0.2.1 (2016-09-26)
==================

* Raise ValueError for URLs like 'http://:8080/'

0.2.0 (2016-09-18)
==================

* Avoid doubling slashes when joining paths (#13)

* Appending path starting from slash is forbidden (#12)

0.1.4 (2016-09-09)
==================

* Add ``kwargs`` support for ``with_query()`` (#10)

0.1.3 (2016-09-07)
==================

* Document ``with_query()``, ``with_fragment()`` and ``origin()``

* Allow ``None`` for ``with_query()`` and ``with_fragment()``

0.1.2 (2016-09-07)
==================

* Fix links, tune docs theme.

0.1.1 (2016-09-06)
==================

* Update README, old version used obsolete API

0.1.0 (2016-09-06)
==================

* The library was deeply refactored, bytes are gone away but all
  accepted strings are encoded if needed.

0.0.1 (2016-08-30)
==================

* The first release.
