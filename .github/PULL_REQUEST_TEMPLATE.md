<!-- Thank you for your contribution! -->

## What do these changes do?

<!-- Please give a short brief about these changes. -->

## Are there changes in behavior for the user?

<!-- Outline any notable behaviour for the end users. -->

## Is it a substantial burden for the maintainers to support this?

<!--
Stop right there! Pause. Just for a minute... Can you think of anything
obvious that would complicate the ongoing development of this project?

Try to consider if you'd be able to maintain it throughout the next
5 years. Does it seem viable? Tell us your thoughts! We'd very much
love to hear what the consequences of merging this patch might be...

This will help us assess if your change is something we'd want to
entertain early in the review process. Thank you in advance!
-->

## Related issue number

<!--
Are there any issues opened that will be resolved by merging this change?
Remember to prefix with 'Fixes' if it closes an issue (e.g. 'Fixes #123').
-->

## Checklist

- [ ] I think the code is well written
- [ ] Unit tests for the changes exist
- [ ] Documentation reflects the changes
- [ ] Add a new news fragment into the `CHANGES/` folder
  * name it `<issue_or_pr_num>.<category>.rst` for example
    (`2023.contrib.rst`)
  * if you don't have an issue number, change it to the pull request
    number after creating the PR
  * ensure category is one of the following:
    * `bugfix`: Signifying a bug fix.
    * `feature`: Signifying a new feature.
    * `deprecation`: Signifying a declaration of future removals and
      breaking changes in behavior.
    * `breaking`: Signifying a breaking change or removal of something
      public.
    * `doc`: Signifying a documentation improvement.
    * `packaging`: Signifying a packaging or tooling change that may be
      relevant to downstreams.
    * `contrib`: Signifying an improvement to the contributor/development
      experience.
    * `misc`: Anything that does not fit the above; usually, something
      not of interest to users.
  * Make sure to use full sentences with correct case and punctuation.
    Explain high-level effects affecting the end-users, for example:
    ```rst
    Test runner no longer crashes when loading non-ASCII contents
    in doctest text files -- by :user:`contributor-gh-handle`.
    ```

    Use the past tense or the present tense in a non-imperative mood,
    referring to what's changed compared to the last released version
    of this project.
