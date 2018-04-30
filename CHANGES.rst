CHANGES
=======

1.2.0 (2018-04-30)
------------------

* Forbid inheritance, replace `__init__` with `__new__` (#171)

* Support PEP-561 (provide type hinting marker) (#182)

1.1.1 (2018-02-17)
------------------

* Fix performance regression: don't encode enmpty netloc (#170)

1.1.0 (2018-01-21)
------------------

* Make pure Python quoter consistent with Cython version (#162)

1.0.0 (2018-01-15)
------------------

* Use fast path if quoted string does not need requoting (#154)

* Speed up quoting/unquoting by `_Quoter` and `_Unquoter` classes (#155)

* Drop `yarl.quote` and `yarl.unquote` public functions (#155)

* Add custom string writer, reuse static buffer if available (#157)
  Code is 50-80 times faster than Pure Python version (was 4-5 times faster)

* Don't recode IP zone (#144)

* Support `encoded=True` in `yarl.URL.build()` (#158)

* Fix updating query with multiple keys (#160)

0.18.0 (2018-01-10)
-------------------

* Fallback to IDNA 2003 if domain name is not IDNA 2008 compatible (#152)

0.17.0 (2017-12-30)
-------------------

* Use IDNA 2008 for domain name processing (#149)

0.16.0 (2017-12-07)
-------------------

* Fix raising `TypeError` by `url.query_string()` after
  `url.with_query({})` (empty mapping) (#141)

0.15.0 (2017-11-23)
-------------------

* Add `raw_path_qs` attribute (#137)

0.14.2 (2017-11-14)
-------------------

* Restore `strict` parameter as no-op in `quote`/`unquote`

0.14.1 (2017-11-13)
-------------------

* Restore `strict` parameter as no-op for sake of compatibility with
  aiohttp 2.2

0.14.0 (2017-11-11)
-------------------

* Drop strict mode (#123)

* Fix `"ValueError: Unallowed PCT %"` when there's a `"%"` in the url (#124)

0.13.0 (2017-10-01)
-------------------

* Document `encoded` parameter (#102)

* Support relative urls like `'?key=value'` (#100)

* Unsafe encoding for QS fixed. Encode `;` char in value param (#104)

* Process passwords without user names (#95)

0.12.0 (2017-06-26)
-------------------

* Properly support paths without leading slash in `URL.with_path()` (#90)

* Enable type annotation checks

0.11.0 (2017-06-26)
-------------------

* Normalize path (#86)

* Clear query and fragment parts in `.with_path()` (#85)

0.10.3 (2017-06-13)
-------------------

* Prevent double URL args unquoting (#83)

0.10.2 (2017-05-05)
-------------------

* Unexpected hash behaviour (#75)


0.10.1 (2017-05-03)
-------------------

* Unexpected compare behaviour (#73)

* Do not quote or unquote + if not a query string. (#74)


0.10.0 (2017-03-14)
-------------------

* Added `URL.build` class method (#58)

* Added `path_qs` attribute (#42)


0.9.8 (2017-02-16)
------------------

* Do not quote ":" in path


0.9.7 (2017-02-16)
------------------

* Load from pickle without _cache (#56)

* Percent-encoded pluses in path variables become spaces (#59)


0.9.6 (2017-02-15)
------------------

* Revert backward incompatible change (BaseURL)


0.9.5 (2017-02-14)
------------------

* Fix BaseURL rich comparison support


0.9.4 (2017-02-14)
------------------

* Use BaseURL


0.9.3 (2017-02-14)
------------------

* Added BaseURL


0.9.2 (2017-02-08)
------------------

* Remove debug print


0.9.1 (2017-02-07)
------------------

* Do not lose tail chars (#45)


0.9.0 (2017-02-07)
------------------

* Allow to quote % in non strict mode (#21)

* Incorrect parsing of query parameters with %3B (;) inside (#34)

* core dumps (#41)

* tmpbuf - compiling error (#43)

* Added `URL.update_path()` method

* Added `URL.update_query()` method (#47)


0.8.1 (2016-12-03)
------------------

* Fix broken aiohttp: revert back `quote` / `unquote`.


0.8.0 (2016-12-03)
------------------

* Support more verbose error messages in `.with_query()` (#24)

* Don't percent-encode `@` and `:` in path (#32)

* Don't expose `yarl.quote` and `yarl.unquote`, these functions are
  part of private API

0.7.1 (2016-11-18)
------------------

* Accept not only `str` but all classes inherited from `str` also (#25)

0.7.0 (2016-11-07)
------------------

* Accept `int` as value for `.with_query()`

0.6.0 (2016-11-07)
------------------

* Explicitly use UTF8 encoding in setup.py (#20)
* Properly unquote non-UTF8 strings (#19)

0.5.3 (2016-11-02)
------------------

* Don't use namedtuple fields but indexes on URL construction

0.5.2 (2016-11-02)
------------------

* Inline `_encode` class method

0.5.1 (2016-11-02)
------------------

* Make URL construction faster by removing extra classmethod calls

0.5.0 (2016-11-02)
------------------

* Add cython optimization for quoting/unquoting
* Provide binary wheels

0.4.3 (2016-09-29)
------------------

* Fix typing stubs

0.4.2 (2016-09-29)
------------------

* Expose quote() and unquote() as public API

0.4.1 (2016-09-28)
------------------

* Support empty values in query ('/path?arg')

0.4.0 (2016-09-27)
------------------

* Introduce relative() (#16)

0.3.2 (2016-09-27)
------------------

* Typo fixes #15

0.3.1 (2016-09-26)
------------------

* Support sequence of pairs as with_query() parameter

0.3.0 (2016-09-26)
------------------

* Introduce is_default_port()

0.2.1 (2016-09-26)
------------------

* Raise ValueError for URLs like 'http://:8080/'

0.2.0 (2016-09-18)
------------------

* Avoid doubling slashes when joining paths (#13)

* Appending path starting from slash is forbidden (#12)

0.1.4 (2016-09-09)
------------------

* Add kwargs support for with_query() (#10)

0.1.3 (2016-09-07)
------------------

* Document with_query(), with_fragment() and origin()

* Allow None for with_query() and with_fragment()

0.1.2 (2016-09-07)
------------------

* Fix links, tune docs theme.

0.1.1 (2016-09-06)
------------------

* Update README, old version used obsolete API

0.1.0 (2016-09-06)
------------------

* The library was deeply refactored, bytes are gone away but all
  accepted strings are encoded if needed.

0.0.1 (2016-08-30)
------------------

* The first release.
