CHANGES
=======

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

* Update REAMDE, old version used obsolete AIP

0.1.0 (2016-09-06)
------------------

* The library was deeply refactored, bytes are gone away but all
  accepted strings are encoded if needed.

0.0.1 (2016-08-30)
------------------

* The first release.
