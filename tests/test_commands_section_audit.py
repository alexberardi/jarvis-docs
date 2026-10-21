"""Tests for the Build -> commands pages after the audit in issue #200 (loop item #396).

The pages describe jarvisd: the node pre-routes and runs commands, jarvisd runs only the model
turn, and samples import from jarvis_command_sdk (not the Python node's own core.* and
services.* modules). These tests pin the fixed facts: no node-only imports in the samples, the
real CLI syntax, the SDK's abstract members and constructor signatures, no old-stack services,
and the jarvisd OAuth flow and token refresh.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES = REPO_ROOT / "docs" / "commands"
SDK_GIT_INSTALL = "pip install git+https://github.com/alexberardi/jarvis-command-sdk.git"


def _page(name):
    return (PAGES / name).read_text(encoding="utf-8")


def _all_pages():
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(PAGES.glob("*.md"))}


def _python_fences(text):
    return re.findall(r"^```python\n(.*?)^```", text, re.S | re.M)


@pytest.fixture(scope="session")
def built_site(tmp_path_factory):
    site_dir = tmp_path_factory.mktemp("site")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "-d", str(site_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return site_dir


def _article(site_dir, *parts):
    html = site_dir.joinpath(*parts).read_text(encoding="utf-8")
    start = html.index("<article")
    return html[start : html.index("</article>", start)]


def test_samples_import_only_from_the_sdk():
    # core.* and services.* exist only inside the Python node, so they break on a desktop agent.
    bad = []
    for name, text in _all_pages().items():
        for fence in _python_fences(text):
            for line in fence.splitlines():
                if re.match(r"\s*(from|import) (core|services|jarvis_log_client)\b", line):
                    bad.append(f"{name}: {line.strip()}")
    assert not bad, bad


def test_full_command_samples_define_every_abstract_member():
    # generate_adapter_examples() is abstract: a class without it can't be instantiated.
    for name, text in _all_pages().items():
        for fence in _python_fences(text):
            if re.search(r"^class \w+\(IJarvisCommand\):", fence, re.M) and "def run(" in fence:
                for member in (
                    "command_name", "description", "keywords", "parameters",
                    "required_secrets", "generate_prompt_examples", "generate_adapter_examples",
                ):
                    assert f"def {member}" in fence, f"{name}: a full sample lacks {member}"


def test_token_bundle_calls_pass_expires_in():
    # TokenBundle.expires_in has no default (jarvis_command_sdk/auth.py).
    for name, text in _all_pages().items():
        for call in re.findall(r"TokenBundle\((.*?)\)\n", text, re.S):
            assert "expires_in" in call, f"{name}: TokenBundle(...) without expires_in"


def test_no_square_bracket_arrays_the_sdk_rejects():
    # Only the date/time arrays accept array[...]; the others raise ValueError.
    text = _page("parameters.md")
    for t in ("string", "int", "float", "bool"):
        assert f'"array[{t}]"' not in text


def test_cli_lines_use_the_real_syntax():
    pages = _all_pages()
    for name, text in pages.items():
        assert "jarvis pantry install" not in text, name
        for line in re.findall(r"utils/set_secret\.py.*", text):
            assert line.startswith("utils/set_secret.py set --key"), f"{name}: {line}"
            assert "--scope node" not in line, name


def test_no_old_stack_services():
    for name, text in _all_pages().items():
        for old in (
            "7703", "7704", "jarvis-command-center", "jarvis-llm-proxy-api",
            "run-docker-dev.sh", "jarvis/blob/main/jarvis-node-setup", "legacy/getting-started",
        ):
            assert old not in text, f"{name} still mentions {old!r}"


def test_command_center_is_not_the_actor():
    # On jarvisd, "command center" is only a module inside jarvisd; the node does the work.
    for name, text in _all_pages().items():
        assert not re.search(r"\bthe command center\b", text, re.I), name
        assert "Response Back to CC" not in text, name


def test_builtin_table_matches_the_node():
    text = _page("index.md")
    builtins = text[text.index("## Built-in Commands") : text.index("## Pantry-Installable Commands")]
    for name in ("tell_joke", "check_alerts", "act_on_items", "control_node", "shopping_list",
                 "todo_list", "export_shopping_list", "export_todo_list", "send_link"):
        assert f"`{name}`" in builtins, name
    for gone in ("get_device_status", "tell_a_joke", "whats_up"):
        assert f"`{gone}`" not in builtins, gone
    assert "GetDeviceStatusCommand" not in "".join(_all_pages().values())


@pytest.mark.parametrize("page", ["index.md", "tutorial-simple.md"])
def test_sdk_install_line(page):
    assert SDK_GIT_INSTALL in _page(page)


def test_node_restart_after_install_command():
    for page in ("index.md", "tutorial-simple.md"):
        assert "systemctl restart jarvis-node" in _page(page), page


def test_oauth_flow_is_jarvisd_side():
    text = _page("tutorial-oauth.md")
    for needle in (
        "/api/v0/oauth/sessions",
        "jarvis/auth/{provider}/ready",
        "/api/v0/oauth/provider/{provider}/credentials",
        "never sees the tokens",
        "Only **one** component per provider",
        "`_base_url`",
    ):
        assert needle in text, needle
    assert "POST /token" not in text
    assert "clear_auth_flag" not in text


def test_token_refresh_section_matches_the_node():
    # jarvis-node-setup agents/token_refresh_agent.py (#160): override when present, else the
    # standard grant; a refresh only the user can fix flags the provider for re-auth.
    text = _page("tutorial-oauth.md")
    refresh = text[text.index("## Background Token Refresh") : text.index("## PKCE Support")]
    for needle in (
        "TokenRefreshAgent",
        "Every 5 minutes",
        "TOKEN_EXPIRES_AT_<PROVIDER>",
        "overrides `refresh_token()`, it calls your override",
        "flags the provider for re-authentication",
        "expires_in=",
    ):
        assert needle in refresh, needle
    ref = _page("interface-reference.md")
    assert "calls your override when you have one" in ref
    assert "jarvisd delivers" in ref or "`jarvisd` delivers" in ref


def test_lifecycle_and_testing_pages_describe_jarvisd(built_site):
    lifecycle = _article(built_site, "commands", "lifecycle", "index.html")
    for needle in ("Who Does What", "pre_route() on the node", "conversation/start", "disabled_pattern_ids"):
        assert needle in lifecycle, needle
    testing = _article(built_site, "commands", "testing", "index.html")
    for needle in ("jarvis_command_center_api_url", "http://&lt;server&gt;:7700",
                   "Full mode is not known to work on jarvisd", "command_confusion_matrix"):
        assert needle in testing, needle


def test_commands_pages_build_and_link(built_site):
    for page in ("index", "interface-reference", "tutorial-simple", "tutorial-api", "tutorial-oauth",
                 "parameters", "secrets", "responses", "lifecycle", "testing"):
        parts = ("commands", "index.html") if page == "index" else ("commands", page, "index.html")
        body = _article(built_site, *parts)
        assert "core.ijarvis" not in body, page
