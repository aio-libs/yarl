# Notes for LLM contributors

## Rule zero: prove it works before opening the PR

**Your job is to deliver code that is proven to work.** If you
have not proven the change works, it is not time to open the PR
yet. "It compiles", "type checks pass", and "the diff looks
right" are not proof. Proof is: the relevant tests run locally
and pass, the new behaviour is exercised by a test you added or
extended, and any user-visible path you touched has been
executed end-to-end. If you cannot run the suite in your
environment, say so explicitly in the PR body rather than
implying coverage you did not actually achieve. Opening a PR
that turns out not to work wastes the reviewer's time and is
the single fastest way to lose trust on this repo.

The rest of this document covers how to dress up that proven
change for review. None of it matters if rule zero is not met.

---

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
without reading the conventions.

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

Pick the number for the fragment filename as follows:

- **If the change has a linked issue, name the fragment after
  the issue number** (e.g. `CHANGES/1234.bugfix.rst` for a fix
  that closes `#1234`). The issue number is stable and known
  before the PR is opened.
- **If there is no linked issue,** you have two options:
  - Open the PR first, then add the fragment as a follow-up
    commit on the same branch using the assigned PR number; or
  - Guess the next PR number (scan
    `gh pr list --state all --limit 5` for the current top of
    the range), include the fragment in your initial push, and
    rename in a follow-up commit if the guess was off by the
    time the PR opened. This PR (`1685.contrib.rst`, opened as
    `#1685`) is an example of the guess-and-pray path working
    on the first try.
- **If both an issue and a PR number are in play and you want
  both to resolve,** keep the issue-numbered file as the real
  fragment and add a symlink at `CHANGES/<pr_number>.<category>.rst`
  pointing to it, so towncrier and the GitHub cross-reference
  both find the entry:

  ```bash
  ln -s 1234.bugfix.rst CHANGES/1240.bugfix.rst
  ```

### 3. Open the PR as a draft, and leave it that way

Use `gh pr create --draft`. **Every LLM-authored submission
must be fully reviewed by a human before it is marked ready
out of draft, with no exceptions.** That review is the
responsibility of the person running the agent, not of the
project maintainers; do not shift the burden of reviewing LLM
work onto them. Maintainers do not look at drafts, so the
draft state is the agent's hand-off to the operator's review,
not a request for the project to review the code on the
operator's behalf. Do not mark the PR ready yourself, and do
not request reviewers from the agent session; the human who
reviewed the change and flipped it out of draft is the one who
routes it.

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
- **Agent output goes in a footer below the PR summary, ideally
  in a collapsed `<details>` block.** The aio-libs template
  sections (What / Are there changes in behavior / etc.) come
  first and read like a human wrote them. Anything the agent
  wants to surface for reviewers (scan results, test logs,
  branch hygiene notes, pipeline output) goes underneath that.
  A collapsed `<details>` block at the very bottom is the
  recommended shape; it keeps the summary readable while still
  letting a curious reviewer expand the agent's work:

  ```markdown
  <details>
  <summary>Agent run details (optional, for reviewers)</summary>

  Tests: <command and result>
  Lint: <command and result>
  </details>
  ```

  What is not OK is mixing this content into the template
  sections themselves, or pushing it above the human-readable
  summary so reviewers have to scroll past it. The shape and
  content of the footer is otherwise up to the agent.
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

### Every line in a test must be covered

The coverage gate applies to test code too, not just `yarl/`. A
test that contains a branch or statement the suite never reaches
will fail CI. This catches a class of mistake agents make all
the time: defensive `raise` inside a monkeypatched stub, a
cleanup branch behind `if had_own_getstate:` that the happy path
never enters, an `else` arm guarding a condition that is always
true under the fixture. From the perspective of a unit suite all
of those lines are dead code, and the coverage report flags them
the same as dead code in `yarl/`.

Design tests so every line runs:

- Drive the fixture deterministically so both arms of any
  conditional are hit, or drop the conditional entirely and
  assert the single shape you actually set up.
- Do not add `raise TypeError("must not be invoked")` guards
  inside stubs the test installs; if the stub is never meant to
  fire, either omit it or assert at the call site that it did
  not. An unreachable `raise` is the most common form of this
  failure.
- Cleanup branches that only run when setup took a particular
  shape (`if had_own_getstate: ...` style restores) need a
  second test, or a parametrize, that exercises the other shape.
  If you cannot justify the second case, unconditionally restore
  instead.
- Prefer `monkeypatch` (which auto-reverts) over hand-rolled
  save/restore blocks; the auto-revert path has no untaken
  branch for coverage to flag.

See [aio-libs/yarl#1687](https://github.com/aio-libs/yarl/pull/1687)
for the canonical example: the test added an unreachable `raise`
inside a patched `__getstate__` and a conditional restore of the
original attribute, both of which CI rejected as uncovered.

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

- Do not open a PR for code you have not proven works (see
  _Rule zero_ at the top of this file). Run the relevant tests,
  cover the new behaviour with a test, exercise the user-visible
  path end-to-end, and say so honestly in the PR body if any of
  that was not possible in your environment.
- Do not invent a `## What / ## Why / ## How / ## Testing` PR
  body; use the aio-libs template above.
- Do not skip the `CHANGES/` fragment "because the change is
  small". Even a one-line bugfix needs one.
- Do not add `Co-Authored-By` trailers for LLM tools, in either
  commits or the PR body.
- Do not mix agent-generated scan output, test summaries, or
  pipeline reports into the template sections. Put them in a
  collapsed `<details>` footer below the PR summary instead.
- Do not use em-dashes or sentence-separating dashes in PR prose
  or commit messages.
- Do not commit Cython build artefacts (`*.c`, `*.html`, `*.so`)
  alongside source changes.
- Do not leave unreachable lines in tests (defensive `raise`
  inside a stub the suite never invokes, cleanup branches that
  only run for a setup shape the test does not exercise). The
  coverage gate applies to test code; see _Every line in a test
  must be covered_ above.
- Do not mark the PR ready for review yourself; that is the
  call of the human running the agent, not the agent itself.
  Maintainers do not look at drafts, but that does not mean
  they should be doing your review; the operator is responsible
  for reviewing the LLM-authored change before flipping the PR
  out of draft.
- Do not request reviewers from the agent session; the human
  who flips the PR out of draft will route it.
