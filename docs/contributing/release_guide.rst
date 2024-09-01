*************
Release Guide
*************

Welcome to the |project| Release Guide!

This page contains information on how to release a new version
of |project| using the automated Continuous Delivery pipeline.

.. tip::

    The intended audience for this document is maintainers
    and core contributors.


Pre-release activities
======================

1. Check if there are any open Pull Requests that could be
   desired in the upcoming release. If there are any — merge
   them. If some are incomplete, try to get them ready.
   Don't forget to review the enclosed change notes per our
   guidelines.
2. Visually inspect the draft section of the :ref:`Changelog`
   page. Make sure the content looks consistent, uses the same
   writing style, targets the end-users and adheres to our
   documented guidelines.
   Most of the changelog sections will typically use the past
   tense or another way to relay the effect of the changes for
   the users, since the previous release.
   It should not target core contributors as the information
   they are normally interested in is already present in the
   Git history.
   Update the changelog fragments if you see any problems with
   this changelog section.
3. Optionally, test the previously published nightlies, that are
   available through GitHub Actions CI/CD artifacts, locally.
4. If you are satisfied with the above, inspect the changelog
   section categories in the draft. Presence of the breaking
   changes or features will hint you what version number
   segment to bump for the release.
5. Update the hardcoded version string in :file:`yarl/__init__.py`.
   Generate a new changelog from the fragments, and commit it
   along with the fragments removal and the Python module changes.
   Use the following commands, don't prepend a leading-``v`` before
   the version number. Just use the raw version number as per
   :pep:`440`.

   .. code-block:: shell-session

       [dir:yarl] $ yarl/__init__.py
       [dir:yarl] $ python -m towncrier build \
                      -- --version 'VERSION_WITHOUT_LEADING_V'
       [dir:yarl] $ git commit -v CHANGES{.rst,/} yarl/__init__.py

.. seealso::

   :ref:`Adding change notes with your PRs`
       Writing beautiful changelogs for humans


The release stage
=================

1. Tag the commit with version and changelog changes, created
   during the preparation stage. If possible, make it GPG-signed.
   Prepend a leading ``v`` before the version number for the tag
   name. Add an extra sentence describing the release contents,
   in a few words.

   .. code-block:: shell-session

       [dir:yarl] $ git tag \
                      -s 'VERSION_WITH_LEADING_V' \
                      -m 'VERSION_WITH_LEADING_V' \
                      -m 'This release does X and Y.'


2. Push that tag to the upstream repository, which ``origin`` is
   considered to be in the example below.

   .. code-block:: shell-session

       [dir:yarl] $ git push origin 'VERSION_WITH_LEADING_V'

3. You can open the `GitHub Actions CI/CD workflow page <GitHub
   Actions CI/CD workflow_>`_ in your web browser to monitor the
   progress. But generally, you don't need to babysit the CI.
4. Check that web page or your email inbox for the notification
   with an approval request. GitHub will send it when it reaches
   the final "publishing" job.
5. Approve the deployment and wait for the CD workflow to complete.
6. Verify that the following things got created:
   - a PyPI release
   - a Git tag
   - a GitHub Releases page
7. Tell everyone you released a new version of |project| :)
   Depending on your mental capacity and the burnout stage, you
   are encouraged to post the updates in issues asking for the
   next release, contributed PRs, Bluesky, Twitter etc. You can
   also call out prominent contributors and thank them!


.. _GitHub Actions CI/CD workflow:
   https://github.com/aio-libs/yarl/actions/workflows/ci-cd.yml
