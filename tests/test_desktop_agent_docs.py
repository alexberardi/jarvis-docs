"""Tests for the desktop agent / browser control pages (loop items #290, #379, #393).

Without the extension's website access, a macro recording captures only page loads and
browser control can't act on pages. These tests pin the pages that say so: they build,
they carry the exact permission steps for Firefox and Chrome, and the install overview, clients
and troubleshooting pages link to them. Since #393 the guide is the Agent tab (docs/agent/);
clients/desktop-agent/ stays as the Install section's short "Add a computer" page.
"""

import html as htmllib
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE = ("clients", "desktop-agent", "index.html")
# The Agent tab's pages, in nav order.
AGENT_PAGES = (
    ("agent", "index.html"),
    ("agent", "pairing", "index.html"),
    ("agent", "macos-permissions", "index.html"),
    ("agent", "browser", "index.html"),
    ("agent", "voice", "index.html"),
    ("agent", "dictation", "index.html"),
    ("agent", "tools", "index.html"),
    ("agent", "updates-settings", "index.html"),
    ("agent", "troubleshooting", "index.html"),
    ("agent", "pi-node", "index.html"),
)


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
    nav = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "clients/desktop-agent.md" in nav
    for parts in AGENT_PAGES:
        assert built_site.joinpath(*parts).exists(), "/".join(parts)
        rel = "/".join(parts[:-1]) + (".md" if len(parts) > 2 else "/index.md")
        assert rel in nav, f"{rel} is not in the nav"


def _agent_bodies(site_dir):
    return "".join(_article(_read(site_dir, *parts)) for parts in AGENT_PAGES)


def test_page_has_the_permission_steps(built_site):
    html = _read(built_site, "agent", "browser", "index.html") + _read(built_site, "agent", "troubleshooting", "index.html")
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
        (("install", "index.html"), "clients/desktop-agent/"),
        (("clients", "index.html"), 'href="../agent/"'),
        (("troubleshooting", "index.html"), "agent/troubleshooting/"),
    ):
        body = _article(_read(built_site, *parts))
        assert link in body, f"{'/'.join(parts)} doesn't link the page"


def test_page_covers_install_pairing_and_permissions(built_site):
    """Loop item #379: the page is the agent's whole user guide, not only the extension.

    Installers per OS from the (pre-)release page, the setup page and its pairing code, the macOS
    permissions, Wayland dictation, both browser extensions, sign-out and self-update, and what is
    still in progress said as such.
    """
    body = _agent_bodies(built_site)
    # The words as a reader sees them: code highlighting splits a command into spans.
    text = htmllib.unescape(re.sub(r"<[^>]+>", "", body))
    for needle in (
        "pre-release",
        "Jarvis-Automation-Agent-",
        "Jarvis-Automation-Agent-Setup-",
        "jarvis-automation-agent_",
        "install-agent.sh",
        "SHA256SUMS",
        "Run anyway",
        "Put a shortcut on the desktop",
        "Show a pairing code",
        "Pending pairings",
        "Approve",
        "Yes, add it",
        "Microphone",
        "Accessibility",
        "Screen Recording",
        "Automation (System Events)",
        "Input Monitoring",
        "restart Jarvis to apply",
        "Wayland",
        "jarvis-agent dictation allow",
        "Firefox",
        "Chrome Web Store",
        "Load unpacked",
        "Sign out of Jarvis Automation",
        "updates itself",
        "In progress",
    ):
        assert needle in text, f"desktop agent page is missing {needle!r}"
    assert 'href="https://github.com/alexberardi/jarvis-server/releases"' in body
    # Only prereleases exist, so GitHub's releases/latest/download/... links 404.
    assert "releases/latest/download" not in body
    for parts, anchor in (
        (("agent", "index.html"), "install"),
        (("agent", "pairing", "index.html"), "pair-this-computer"),
        (("agent", "macos-permissions", "index.html"), "macos-permissions"),
        (("agent", "browser", "index.html"), "turn-on-website-access"),
        (("agent", "troubleshooting", "index.html"), "troubleshooting"),
    ):
        assert f'id="{anchor}"' in _read(built_site, *parts), f"{'/'.join(parts)} has no #{anchor}"
