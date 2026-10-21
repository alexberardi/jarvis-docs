"""Tests for the command-building docs on jarvisd (loop item #385).

Under jarvisd, SDK packages run on the Python node and on desktop agents but not yet on the Go
Pi node, Pi-only packages are kept off computers, prompt providers are not supported, and
`jdt deploy docker` targets the legacy Docker stack. These tests pin the "Where your code runs"
page that says so, its links, the notes on the prompt-provider and deploy pages, and the SDK's
git install line (the package is not on PyPI).
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
PAGE = ("extending", "where-code-runs", "index.html")
SDK_GIT_INSTALL = "pip install git+https://github.com/alexberardi/jarvis-command-sdk.git"


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
    # Only the page body: the nav sidebar links every page from every page.
    html = site_dir.joinpath(*parts).read_text(encoding="utf-8")
    start = html.index("<article")
    return html[start : html.index("</article>", start)]


def test_page_is_built_and_in_nav(built_site):
    assert built_site.joinpath(*PAGE).exists()
    assert "extending/where-code-runs.md" in (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def test_page_says_where_packages_run(built_site):
    body = _article(built_site, *PAGE)
    for needle in (
        "Where your code runs",
        "pre-release",
        "Python node",
        "desktop agent",
        "Go voice node",
        "install-pi.sh",
        "Not supported yet",
        "not yet checked on a Pi",
        "targets",
        "apt_packages",
        "platforms",
        "made for Pi nodes, not computers",
        "needs system packages that only a Pi node installs",
        "skipped_components",
    ):
        assert needle in body, f"where-code-runs page is missing {needle!r}"
    # The Go node runs packages in a Python sidecar (built, not checked on a Pi): never "doesn't run".
    assert "doesn't run SDK packages" not in body
    assert "Nothing yet" not in body


def test_page_is_linked_from_build_and_commands(built_site):
    for parts in (("extending", "index.html"), ("commands", "index.html")):
        assert "where-code-runs/" in _article(built_site, *parts), f"{'/'.join(parts)} doesn't link the page"


@pytest.mark.parametrize(
    "parts",
    [
        ("extending", "prompt-providers", "index.html"),
        ("extending", "prompt-providers", "reference", "index.html"),
    ],
)
def test_prompt_provider_pages_say_unsupported_on_jarvisd(built_site, parts):
    body = _article(built_site, *parts)
    assert "Not supported on jarvisd" in body
    assert "legacy/" in body


def test_deploy_page_marks_docker_target_legacy(built_site):
    body = _article(built_site, "extending", "toolkit", "deploy", "index.html")
    docker = body[body.index('id="jdt-deploy-docker"') :]
    docker = docker[: docker.index('id="jdt-deploy-ssh"')]
    assert "legacy" in docker.lower()
    assert "legacy/" in docker


def test_sdk_install_line_is_the_git_install():
    stale = []
    for path in DOCS.rglob("*.md"):
        if "legacy" in path.relative_to(DOCS).parts:
            continue
        if "pip install jarvis-command-sdk" in path.read_text(encoding="utf-8"):
            stale.append(str(path.relative_to(REPO_ROOT)))
    assert not stale, f"PyPI install line (the SDK is not on PyPI) in: {stale}"
    assert SDK_GIT_INSTALL in (DOCS / "libraries" / "command-sdk.md").read_text(encoding="utf-8")
