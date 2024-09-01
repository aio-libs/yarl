"""Data conversion helpers for the in-tree PEP 517 build backend."""

from itertools import chain
from re import sub as _substitute_with_regexp


def _emit_opt_pairs(opt_pair):
    flag, flag_value = opt_pair
    flag_opt = f"--{flag!s}"
    if isinstance(flag_value, dict):
        sub_pairs = flag_value.items()
    else:
        sub_pairs = ((flag_value,),)

    yield from ("=".join(map(str, (flag_opt,) + pair)) for pair in sub_pairs)


def get_cli_kwargs_from_config(kwargs_map):
    """Make a list of options with values from config."""
    return list(chain.from_iterable(map(_emit_opt_pairs, kwargs_map.items())))


def get_enabled_cli_flags_from_config(flags_map):
    """Make a list of enabled boolean flags from config."""
    return [f"--{flag}" for flag, is_enabled in flags_map.items() if is_enabled]


def sanitize_rst_roles(rst_source_text: str) -> str:
    """Replace RST roles with inline highlighting."""
    pep_role_regex = r"""(?x)
        :pep:`(?P<pep_number>\d+)`
    """
    pep_substitution_pattern = (
        r"`PEP \g<pep_number> <https://peps.python.org/pep-\g<pep_number>>`__"
    )

    user_role_regex = r"""(?x)
        :user:`(?P<github_username>[^`]+)(?:\s+(.*))?`
    """
    user_substitution_pattern = (
        r"`@\g<github_username> "
        r"<https://github.com/sponsors/\g<github_username>>`__"
    )

    issue_role_regex = r"""(?x)
        :issue:`(?P<issue_number>[^`]+)(?:\s+(.*))?`
    """
    issue_substitution_pattern = (
        r"`#\g<issue_number> "
        r"<https://github.com/aio-libs/yarl/issues/\g<issue_number>>`__"
    )

    pr_role_regex = r"""(?x)
        :pr:`(?P<pr_number>[^`]+)(?:\s+(.*))?`
    """
    pr_substitution_pattern = (
        r"`PR #\g<pr_number> "
        r"<https://github.com/aio-libs/yarl/pull/\g<pr_number>>`__"
    )

    commit_role_regex = r"""(?x)
        :commit:`(?P<commit_sha>[^`]+)(?:\s+(.*))?`
    """
    commit_substitution_pattern = (
        r"`\g<commit_sha> "
        r"<https://github.com/aio-libs/yarl/commit/\g<commit_sha>>`__"
    )

    gh_role_regex = r"""(?x)
        :gh:`(?P<gh_slug>[^`<]+)(?:\s+([^`]*))?`
    """
    gh_substitution_pattern = r"GitHub: ``\g<gh_slug>``"

    meth_role_regex = r"""(?x)
        (?::py)?:meth:`~?(?P<rendered_text>[^`<]+)(?:\s+([^`]*))?`
    """
    meth_substitution_pattern = r"``\g<rendered_text>()``"

    role_regex = r"""(?x)
        (?::\w+)?:\w+:`(?P<rendered_text>[^`<]+)(?:\s+([^`]*))?`
    """
    substitution_pattern = r"``\g<rendered_text>``"

    project_substitution_regex = r"\|project\|"
    project_substitution_pattern = "yarl"

    substitutions = (
        (pep_role_regex, pep_substitution_pattern),
        (user_role_regex, user_substitution_pattern),
        (issue_role_regex, issue_substitution_pattern),
        (pr_role_regex, pr_substitution_pattern),
        (commit_role_regex, commit_substitution_pattern),
        (gh_role_regex, gh_substitution_pattern),
        (meth_role_regex, meth_substitution_pattern),
        (role_regex, substitution_pattern),
        (project_substitution_regex, project_substitution_pattern),
    )

    rst_source_normalized_text = rst_source_text
    for regex, substitution in substitutions:
        rst_source_normalized_text = _substitute_with_regexp(
            regex,
            substitution,
            rst_source_normalized_text,
        )

    return rst_source_normalized_text
