"""Tests for the Install section and the home page on jarvisd (loop item #378).

The option lists are checked against the install scripts' own headers:
fixtures/install-sh-options.txt and fixtures/install-ps1-options.txt are the option blocks of
jarvis-server's scripts/install.sh and scripts/install.ps1, copied verbatim (jarvis-server main at
c49c72a, 2026-10-21). When a script's options change, copy its block again and these tests name
what the page is missing.
"""

import re
from pathlib import Path

from test_site_structure import RELEASES, _url_dir, built_site  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SH_OPTIONS = (FIXTURES / "install-sh-options.txt").read_text(encoding="utf-8")
PS1_OPTIONS = (FIXTURES / "install-ps1-options.txt").read_text(encoding="utf-8")

# The pages this item fills. voice-node, mobile-app, migrate and unraid belong to other items.
FILLED = [
    "install/macos.md",
    "install/windows.md",
    "install/linux.md",
    "install/one-liners.md",
    "install/setup-wizard.md",
    "install/upgrade.md",
    "install/uninstall.md",
]
SERVER_ASSETS = {
    "install/macos.md": ["Jarvis-Automation-Server-<version>.dmg"],
    "install/windows.md": ["Jarvis-Automation-Server-Setup-<version>.exe"],
    "install/linux.md": [
        "jarvis-automation-server_<version>_amd64.deb",
        "jarvis-automation-server_<version>_arm64.deb",
    ],
}
DATA_PAGE = "../operate/data-and-backups.md"


def _text(md):
    return (DOCS / md).read_text(encoding="utf-8")


def _html(site, md):
    return (site / _url_dir(md) / "index.html").read_text(encoding="utf-8")


def test_install_pages_are_filled(built_site):
    for md in FILLED:
        text = _text(md)
        assert "stub" not in text.lower() and "on its way" not in text, f"{md} is still a stub"
        assert len(text.splitlines()) > 20, f"{md} is too short to be the guide"
        assert "pre-release" in text.lower() and RELEASES in text, md
        assert (built_site / _url_dir(md) / "index.html").exists()


def test_os_pages_name_their_installer_and_lead_to_the_wizard():
    for md, assets in SERVER_ASSETS.items():
        text = _text(md)
        for asset in assets:
            assert asset in text, f"{md} doesn't name {asset}"
        assert "setup-wizard.md" in text, f"{md} doesn't lead on to the setup wizard"
        assert "one-liners.md" in text, f"{md} doesn't point at the install scripts"
        assert DATA_PAGE in text, f"{md} doesn't link where the data lives"


def test_os_pages_put_the_installer_before_the_terminal():
    """Installers first, then the one-liners: the installer is named before any shell command."""
    for md, assets in SERVER_ASSETS.items():
        text = _text(md)
        first_fence = text.find("```")
        if first_fence != -1:
            assert text.find(assets[0]) < first_fence, f"{md} shows a command before its installer"


def test_macos_page():
    text = _text("install/macos.md")
    assert "Apple silicon" in text and "Intel" in text
    assert "notarized" in text
    assert "Option" in text and "Uninstall" in text


def test_windows_page():
    text = _text("install/windows.md")
    assert "Windows protected your PC" in text and "Run anyway" in text
    assert "SHA256SUMS" in text
    assert "%ProgramData%\\jarvisd" in text


def test_linux_page():
    text = _text("install/linux.md")
    assert "sudo apt install ./jarvis-automation-server_" in text
    assert "--user" in text
    assert "/var/lib/jarvisd" in text
    assert "systemd" in text


def _flags(options, prefix):
    return sorted(set(re.findall(rf"(?m)^#\s+({prefix}[A-Za-z][A-Za-z-]*)", options)))


def test_fixtures_hold_the_option_blocks():
    assert _flags(SH_OPTIONS, "--") == sorted(
        ["--base-url", "--force", "--purge", "--stop-legacy", "--uninstall", "--user", "--version", "--yes"]
    )
    assert _flags(PS1_OPTIONS, "-") == sorted(
        ["-BaseUrl", "-Force", "-Purge", "-StopLegacy", "-Uninstall", "-Yes"]
    )


def test_one_liners_list_every_script_option():
    text = _text("install/one-liners.md")
    for flag in _flags(SH_OPTIONS, "--"):
        assert f"`{flag}" in text, f"one-liners.md doesn't list install.sh {flag}"
    for flag in _flags(PS1_OPTIONS, "-") + ["-Version"]:
        assert f"`{flag}" in text, f"one-liners.md doesn't list install.ps1 {flag}"
    for env in ["JARVISD_VERSION", "JARVISD_YES"]:
        assert env in text, f"one-liners.md doesn't say {env} sets an option under irm | iex"


def test_one_liners_show_pinned_commands_and_verification():
    text = _text("install/one-liners.md")
    pinned = "https://github.com/alexberardi/jarvis-server/releases/download/v0.1.0-rc18.6/"
    assert f"{pinned}install.sh" in text
    assert f"{pinned}install.ps1" in text
    assert "SHA256SUMS.minisig" in text and "minisign -V" in text
    # The project key, exactly as install.sh and jarvisd trust it.
    assert "RWRyW6ICtU+iyX4p4RnS24ju0gRsWpxvv6B8pI9G+ZS01q8t8oupAQ8L" in text
    assert ":7710/setup#token=" in text


def test_setup_wizard_page():
    text = _text("install/setup-wizard.md")
    assert "jarvisd setup-link" in text and "--qr" in text
    assert "setup token" in text.lower() and "setup-token" in text
    for step in ["Check", "Account", "Hardware", "Language model", "Speech-to-text", "Voice",
                 "Voice recognition", "Memory & search", "Privacy", "This computer", "Done"]:
        assert f"**{step}**" in text, f"setup-wizard.md doesn't describe the {step} step"
    assert "7700" in text  # where nodes and the app point afterwards


def test_upgrade_page():
    text = _text("install/upgrade.md")
    assert "**Update now**" in text  # the Updates page's button (UpdatePage.tsx)
    assert "jarvisd upgrade" in text and "--rollback" in text
    assert "backups/" in text and "jarvisd.prev" in text
    assert DATA_PAGE in text


def test_uninstall_page():
    text = _text("install/uninstall.md")
    assert "Option" in text and "Uninstall" in text
    assert "--uninstall" in text and "--purge" in text
    assert "-Uninstall" in text and "-Purge" in text
    assert "apt purge jarvis-automation-server" in text
    assert "Apps" in text  # Windows: Settings > Apps
    assert DATA_PAGE in text


def test_home_page_has_no_microservice_diagram():
    text = _text("index.md")
    assert "```mermaid" not in text
    for retired in ["Command Center", "Whisper API", "LLM Proxy", "jarvis-admin"]:
        assert retired not in text, f"index.md still mentions {retired}"


def test_home_page_has_the_three_cards(built_site):
    text = _text("index.md")
    assert '<div class="grid cards start-cards" markdown>' in text
    for title, target in [
        ("Install the server", "install/index.md"),
        ("Add a computer", "clients/desktop-agent.md"),
        ("Add a voice node", "install/voice-node.md"),
    ]:
        assert title in text, f"index.md has no '{title}' card"
        assert f"({target})" in text, f"index.md doesn't link {target}"
    html = (built_site / "index.html").read_text(encoding="utf-8")
    assert 'class="grid cards start-cards"' in html
    for href in ["install/", "clients/desktop-agent/", "install/voice-node/"]:
        assert f'href="{href}"' in html, f"the built home page doesn't link {href}"
