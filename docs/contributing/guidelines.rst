-----------------
Contributing docs
-----------------

We use Sphinx_ to generate our docs website. You can trigger
the process locally by executing:

     .. code-block:: shell-session

        $ make doc

It is also integrated with `Read The Docs`_ that builds and
publishes each commit to the main branch and generates live
docs previews for each pull request.

The sources of the Sphinx_ documents use reStructuredText as a
de-facto standard. But in order to make contributing docs more
beginner-friendly, we've integrated `MyST parser`_ allowing us
to also accept new documents written in an extended version of
Markdown that supports using Sphinx directives and roles. `Read
the docs <MyST docs_>`_ to learn more on how to use it.

.. _MyST docs: https://myst-parser.readthedocs.io/en/latest/using/intro.html#writing-myst-in-sphinx
.. _MyST parser: https://pypi.org/project/myst-parser/
.. _Read The Docs: https://readthedocs.org
.. _Sphinx: https://www.sphinx-doc.org

.. include:: ../../CHANGES/README.rst
