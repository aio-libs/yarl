CHANGES
=======

0.9.3 (2017-02-14)
------------------

* Added BaseURL


0.9.2 (2017-02-08)
------------------

* Remove debug print


0.9.1 (2017-02-07)
------------------

* Do not lose tail chars #45


0.9.0 (2017-02-07)
------------------

* Allow to quote % in non strict mode #21

* Incorrect parsing of query parameters with %3B (;) inside #34

* core dumps #41

* tmpbuf - compiling error #43

* Added `URL.update_path()` method

* Added `URL.update_query()` method #47


0.8.1 (2016-12-03)
------------------

* Fix broken aiohttp: revert back `quote` / `unquote`.


0.8.0 (2016-12-03)
------------------

* Support more verbose error messages in `.with_query()` #24

* Don't percent-encode `@` and `:` in path #32

* Don't expose `yarl.quote` and `yarl.unquote`, these functions are
  part of private API

0.7.1 (2016-11-18)
------------------

* Accept not only `str` but all classes inherited from `str` also #25

0.7.0 (2016-11-07)
------------------

* Accept `int` as value for `.with_query()`

0.6.0 (2016-11-07)
------------------

* Explicitly use UTF8 encoding in setup.py #20
* Properly unquote non-UTF8 strings #19

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

* Introduce relative() #16

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

* Avoid doubling slashes when joining paths #13

* Appending path starting from slash is forbidden #12

0.1.4 (2016-09-09)
------------------

* Add kwargs support for with_query() #10

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
