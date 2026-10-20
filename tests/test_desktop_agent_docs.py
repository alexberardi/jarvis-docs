"""Tests for the desktop agent / browser control page (loop item #290).

Without the extension's website access, a macro recording captures only page loads and
browser control can't act on pages. These tests pin the page that says so: it builds,
it carries the exact permission steps for Firefox and Chrome, and the install, clients
and troubleshooting pages link to it.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE = ("clients", "desktop-agent", "index.html")


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


def _read(site_dir, *parts):
    return site_dir.joinpath(*parts).read_text(encoding="utf-8")


def test_page_is_built_and_in_nav(built_site):
    assert built_site.joinpath(*PAGE).exists()
    assert "clients/desktop-agent.md" in (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def test_page_has_the_permission_steps(built_site):
    html = _read(built_site, *PAGE)
    for needle in (
        "jarvis-agent browser install",
        "jarvis-agent browser status",
        "about:addons",
        "Access your data for all websites",
        "Site access",
        "On all sites",
        "Run in Private Windows",
        "Allow in Incognito",
        "reload",
        "Clicked",
        "Opened",
    ):
        assert needle in html, f"desktop agent page is missing {needle!r}"


def _article(html):
    # Only the page body: the nav sidebar links desktop-agent/ on every page.
    start = html.index("<article")
    return html[start : html.index("</article>", start)]


def test_page_is_linked_from_install_clients_and_troubleshooting(built_site):
    for parts, link in (
        (("getting-started", "installation", "index.html"), "clients/desktop-agent/"),
        (("clients", "index.html"), 'href="desktop-agent/"'),
        (("troubleshooting", "index.html"), "clients/desktop-agent/#troubleshooting"),
    ):
        body = _article(_read(built_site, *parts))
        assert link in body, f"{'/'.join(parts)} doesn't link the page"
