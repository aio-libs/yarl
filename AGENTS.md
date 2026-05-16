# Notes for LLM contributors

Read this before opening a pull request against `aio-libs/yarl`.
Agents keep getting the same things wrong in this repo, so the
rules below are not optional. If you are about to skip a section
because it sounds boilerplate, that is exactly the section to
re-read.

Human-facing contributor docs live under
[docs/contributing/](docs/contributing/) and
[CHANGES/README.rst](CHANGES/README.rst); this file is the short
orientation for agents.

## What this project is

`yarl` is the URL parsing and building library used by `aiohttp`
and the rest of the `aio-libs` stack. It is small, widely
deployed, and performance sensitive. The pure-Python code lives
under `yarl/` and the quoting hot path is Cythonized
(`yarl/_quoting_c.pyx`, with a pure-Python equivalent at
`yarl/_quoting_py.py`).

Useful entry points:

| Path                    | What                                                   |
| ----------------------- | ------------------------------------------------------ |
| `yarl/_url.py`          | `URL` class, all public API                            |
| `yarl/_parse.py`        | `split_url` / `split_netloc`, RFC 3986 parsing         |
| `yarl/_path.py`         | path normalisation helpers                             |
| `yarl/_query.py`        | query string assembly / encoding                       |
| `yarl/_quoting.py`      | dispatcher between the C and Python quoters            |
| `yarl/_quoting_c.pyx`   | Cython quoter (hot path; ships in wheels)              |
| `yarl/_quoting_py.py`   | pure-Python quoter (used when the extension is absent) |
| `yarl/_quoters.py`      | pre-built quoter instances reused across the codebase  |
| `tests/`                | pytest suite, including the benchmarks                 |
| `CHANGES/`              | towncrier news fragments, one per PR                   |
| `docs/`                 | Sphinx docs source                                     |
| `packaging/`            | in-tree PEP 517 backend that drives `cythonize`        |

## Pull request rules

These are the rules agents most often violate. Treat them as
mandatory.

### 1. Use the aio-libs pull request template

`yarl` follows the standard `aio-libs` PR template. Even though
the repo does not ship its own `.github/PULL_REQUEST_TEMPLATE.md`,
maintainers expect every PR body to follow this exact structure.
Do not invent your own `## What / ## Why / ## How / ## Testing`
layout; that is the marker that the PR was written by an agent
without reading the conventions. See the cautionary example at
[aio-libs/multidict#1336](https://github.com/aio-libs/multidict/pull/1336)
for a PR that was closed for this reason.

Fill out the template verbatim, like so:

```markdown
<!-- Thank you for your contribution! -->

## What do these changes do?

<short prose describing the change>

## Are there changes in behavior for the user?

<yes or no, plus a sentence if yes>

## Is it a substantial burden for the maintainers to support this?

<no, plus a sentence on why if relevant>

## Related issue number

Fixes #NNNN
<!-- or a bare reference if the change is related but does not close -->

## Checklist

- [x] I think the code is well written
- [x] Unit tests for the changes exist
- [x] Documentation reflects the changes
- [ ] If you provide code modification, please add yourself to `CONTRIBUTORS.txt`
- [x] Add a new news fragment into the `CHANGES/` folder
```

Tick the boxes that actually apply. If a row does not apply
(e.g. CI-only change with no tests), write `N/A` next to it
rather than silently leaving it blank.

For a real filled-out example in this repo, see
[aio-libs/yarl#1681](https://github.com/aio-libs/yarl/pull/1681).

### 2. Add a CHANGES fragment

Every user-visible PR needs a towncrier news fragment in
`CHANGES/`, named `<pr_number>.<category>.rst`. Categories
(defined in [CHANGES/README.rst](CHANGES/README.rst)):

| Category       | When to use                                                     |
| -------------- | --------------------------------------------------------------- |
| `bugfix`       | corrects undesired behaviour                                    |
| `feature`      | new public API or behaviour                                     |
| `deprecation`  | announces a future removal                                      |
| `breaking`     | removes or changes something public in a breaking way           |
| `doc`          | documentation structure or build process                        |
| `packaging`    | downstream-visible packaging or build changes                   |
| `contrib`      | contributor experience (CI, dev env, test invocation)           |
| `misc`         | does not fit any of the above                                   |

Conventions for the fragment body:

- Use the past tense (`Fixed`, `Added`, `Bumped`), since it is
  read as a "what changed since the previous release" digest.
- Use reStructuredText, not Markdown.
- Do not include the issue or PR number in the body; towncrier
  adds it automatically from the filename.
- Sign with `-- by :user:\`github-handle\`` at the end.

Example (`CHANGES/1654.bugfix.rst` style):

```rst
Rejected URLs containing text before the opening bracket in the
host component (e.g. ``http://127.0.0.1[aa::ff]``), which were
previously parsed by silently dropping the prefix
-- by :user:`github-handle`.
```

You do not know the PR number before pushing. Open the PR first
to get the number, then rename the file in a follow-up commit on
the same branch (or use the issue number if one exists).

### 3. Open the PR as a draft

Use `gh pr create --draft`. The maintainer will mark it ready
once they have looked it over. Do not request reviewers yourself.

### 4. Disclose the agent, do not advertise it

Disclosure is required, advertising is not welcome. Put one
plain line at the bottom of the PR body naming the agent that
drafted the change, for example:

```
Drafted with <agent name and version>; reviewed by <human handle>.
```

That single line is enough. Beyond that:

- **No `Co-Authored-By:` trailers** for an LLM or any AI tool,
  in commits or in the PR body. Attribution goes to the human
  who reviewed the change.
- No "Generated by", "Quality Report", "Test summary by
  <agent>", or similar footers in the PR body. The closed
  `aio-libs/multidict#1336` had exactly this kind of footer and
  it was the giveaway that closed the PR.
- No `🤖`, `✨`, `🚀` emoji decoration in commit messages, PR
  titles, PR bodies, or news fragments. Project style is plain
  prose.
- Commit messages and PR prose should read as if a human
  contributor wrote them. Specifically:
  - **No em-dashes (`—`)** and no dashes used as sentence
    separators (`foo - bar`). Use a semicolon or a comma. This
    is the strongest tell for AI-generated prose in this
    project, and reviewers do read for it.
  - No "Let me", "I'll", or first-person narration of what the
    agent did. Describe the change, not the author.
  - No filler sections ("Overview", "Summary of changes",
    "Key takeaways") on top of the template. The template
    already has the right sections.

### 5. Keep the PR body short

A couple of sentences per template section is plenty. If the
change is non-obvious, a short reproducer or a paragraph on root
cause is welcome (see
[aio-libs/yarl#1654](https://github.com/aio-libs/yarl/pull/1654)
for the right length). Long, multi-section essays with bolded
sub-headings are not the style here.

### 6. Commit hygiene

- One logical change per PR. If a refactor and a bugfix are
  bundled together, split them.
- Pre-commit auto-fixes (`ruff`, `ruff format`, pyupgrade,
  trailing-whitespace, end-of-file-fixer) run on commit and
  rewrite files in place; when a hook rewrites a file the commit
  aborts, so re-stage and commit again.
- The repo does **not** use Conventional Commits as a CI gate.
  Recent landed subjects are short imperative or descriptive
  prose (e.g. `Reject URLs with text before bracket in host`,
  `ci: switch typing coverage tracking to Coveralls`, `docs:
  note UUID-to-int coercion in with_query docs`). Match that
  style; do not force `feat:` / `fix:` prefixes onto every
  commit.

## Tests

Install dev deps and run the suite:

```bash
make .develop      # installs deps and builds the Cython extension in place
pytest ./tests ./yarl
```

Or use the Makefile targets directly: `make test` runs lint and
then pytest, `make cov` adds coverage, `make vtest` is verbose.
`make fmt` runs pre-commit across the tree.

CI runs the full matrix across the supported Python versions
plus a wheel build, doctests, spellcheck, and a CodSpeed
benchmark leg for the quoting hot path. Do not regress
`tests/test_quoting_benchmarks.py` or
`tests/test_url_benchmarks.py` without flagging the trade-off in
the PR body.

## Cython quoter

`yarl/_quoting_c.pyx` is the compiled quoter; `yarl/_quoting_py.py`
is the pure-Python equivalent. They must stay behaviourally
identical: any change to one must land in the other in the same
PR, and the tests under `tests/test_quoting.py` exercise both
paths. If you change the public quoting surface, update the
dispatcher in `yarl/_quoting.py` too.

Generated files (`yarl/*.c`, `yarl/*.html`, the built `*.so`) are
build outputs; do not commit them. `make cythonize` regenerates
the `.c` siblings of the `.pyx` sources during development.

## Documentation

User-visible API changes need a docs update under `docs/` (the
relevant section of `docs/api.rst` plus any narrative pages). The
docstring goes in the code; the prose context goes in the Sphinx
sources. `make doc` builds the docs locally; `make doctest`
exercises the runnable examples in the docs.

## Things not to do

- Do not invent a `## What / ## Why / ## How / ## Testing` PR
  body; use the aio-libs template above.
- Do not skip the `CHANGES/` fragment "because the change is
  small". Even a one-line bugfix needs one.
- Do not add `Co-Authored-By` trailers for LLM tools, in either
  commits or the PR body.
- Do not paste an agent-generated "Quality Report", "Test plan
  summary", or "Generated by <pipeline>" block at the bottom of
  the PR body. A one-line disclosure naming the agent is fine
  and expected; a marketing footer is not.
- Do not use em-dashes or sentence-separating dashes in PR prose
  or commit messages.
- Do not commit Cython build artefacts (`*.c`, `*.html`, `*.so`)
  alongside source changes.
- Do not request reviewers from the agent session; leave the PR
  as a draft and let the maintainer route it.
