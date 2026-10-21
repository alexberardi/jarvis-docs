"""Tests for the Operate section on jarvisd (loop item #382).

The jarvisd CLI reference is checked against jarvisd's own usage text:
fixtures/jarvisd-usage.txt is the `usage` constant of jarvis-server's cmd/jarvisd/main.go,
copied verbatim (jarvis-server main at 507a55a, 2026-10-21; unchanged since v0.1.0-rc18).
When jarvisd's usage changes, copy it again and these tests name what the page is missing.
"""

import re
from pathlib import Path

import pytest

from test_site_structure import _nav_paths, _read, _section, _url_dir, config, built_site  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
USAGE = (Path(__file__).resolve().parent / "fixtures" / "jarvisd-usage.txt").read_text(encoding="utf-8")

CLI = "operate/cli.md"
DATA = "operate/data-and-backups.md"
NETWORK = "operate/network.md"
OFFLINE = "security/offline-mode.md"
TROUBLESHOOTING = "troubleshooting/index.md"
OPERATE_PAGES = ["operate/index.md", CLI, DATA, NETWORK, OFFLINE, TROUBLESHOOTING]


def _text(md):
    return (DOCS / md).read_text(encoding="utf-8")


def _usage_commands():
    """The command phrases in the usage text: "serve", "service install", "service start", ..."""
    phrases = []
    body = USAGE.split("commands:", 1)[1].split("\n\n--home", 1)[0]
    for line in body.splitlines():
        m = re.match(r"^  ([a-z][a-z|-]*(?: [a-z][a-z|-]*)?)(?:\s|$)", line)
        if not m:
            continue
        words = m.group(1).split(" ")
        if len(words) == 2 and words[0] not in ("service", "migrate"):
            words = words[:1]  # "setup-link       print ..." is a command and its help
        last = words[-1].split("|")
        phrases += [" ".join(words[:-1] + [w]) for w in last]
    return phrases


def _usage_flags():
    return sorted(set(re.findall(r"--[a-z][a-z-]*", USAGE)))


def test_usage_fixture_parses():
    commands = _usage_commands()
    for want in ("serve", "upgrade", "service install", "service uninstall", "service start", "service stop",
                 "service restart", "service status", "setup-link", "install-from-app", "migrate status",
                 "import-recipes", "import-legacy", "doctor", "version"):
        assert want in commands, f"{want!r} not parsed from the usage fixture: {commands}"
    assert "--fix" in _usage_flags() and "--home" in _usage_flags()


@pytest.mark.parametrize("command", _usage_commands())
def test_cli_page_documents_every_command(command):
    assert f"jarvisd {command}" in _text(CLI), f"{CLI} doesn't document `jarvisd {command}`"


def test_cli_page_documents_every_flag():
    text = _text(CLI)
    missing = [flag for flag in _usage_flags() if f"`{flag}" not in text and f" {flag}" not in text]
    assert not missing, f"{CLI} doesn't mention: {missing}"


def test_cli_page_documents_the_env_file_and_home():
    text = _text(CLI)
    for want in ("JARVIS_HOME", "jarvisd.env", "/etc/jarvisd/jarvisd.env", "~/.jarvisd"):
        assert want in text, f"{CLI} doesn't mention {want}"


def test_operate_nav(config):  # noqa: F811
    paths = list(_nav_paths(_section(config["nav"], "Operate")))
    for md in OPERATE_PAGES:
        assert md in paths, f"{md} not in the Operate nav"
    assert "reference/env-vars.md" not in paths
    legacy = set(_nav_paths(_section(config["nav"], "Legacy")))
    assert "legacy/reference/env-vars.md" in legacy
    assert "legacy/troubleshooting.md" in legacy


def test_operate_pages_build_and_are_indexed(built_site):  # noqa: F811
    for md in OPERATE_PAGES:
        html = _read(built_site, *_url_dir(md).parts, "index.html")
        assert 'content="noindex"' not in html, f"{md} is noindex"
        assert "legacy-banner" not in html, f"{md} has the legacy banner"


def test_operate_index_says_pre_release():
    text = _text("operate/index.md")
    assert "pre-release" in text.lower()
    assert "https://github.com/alexberardi/jarvis-server/releases" in text
    for md in (CLI, DATA, NETWORK):
        assert Path(md).name in text, f"operate/index.md doesn't link {md}"


def test_data_page_names_each_os_home_and_the_backups():
    text = _text(DATA)
    for want in ("/var/lib/jarvisd", "~/.jarvisd", r"%ProgramData%\jarvisd", "jarvis.db", "backups",
                 "jarvisd.prev", "jarvisd service stop"):
        assert want in text, f"{DATA} doesn't mention {want}"


def test_network_page_names_the_ports_and_mdns():
    text = _text(NETWORK)
    for want in ("7700", "7710", "1884", "5353", "9883", "_jarvis-config._tcp", "server.legacy_ports",
                 "JARVIS_LEGACY_PORTS", "jarvisd doctor --fix", "--port-offset", "JARVIS_MDNS"):
        assert want in text, f"{NETWORK} doesn't mention {want}"


def test_legacy_port_switch_is_documented_as_next_release_only():
    """rc18 always opens the legacy ports; server.legacy_ports and JARVIS_LEGACY_PORTS come after it."""
    network = _text(NETWORK)
    assert "three TCP ports" not in network, f"{NETWORK} describes the post-rc18 layout as current"
    assert "rc18 always opens" in network, f"{NETWORK} doesn't say rc18 always opens the legacy ports"
    for md in (NETWORK, TROUBLESHOOTING):
        text = _text(md)
        for line in text.splitlines():
            if "legacy_ports" in line or "LEGACY_PORTS" in line:
                assert "next release" in line, f"{md} presents the legacy-port switch as current: {line.strip()}"
    trouble = _text(TROUBLESHOOTING)
    assert "all 3 TCP ports" not in trouble or "next release" in trouble.split("all 3 TCP ports")[0][-400:], \
        f"{TROUBLESHOOTING}'s sample doctor output shows the post-rc18 layout unlabelled"


def test_offline_mode_is_about_jarvisd():
    text = _text(OFFLINE)
    for gone in ("MinIO", "PostgreSQL", "Redis", "Loki", "config-service", "~/.jarvis/", "docker"):
        assert gone not in text, f"{OFFLINE} still mentions {gone}"
    for want in ("updates.enabled", "updates.allow_check", "web_search.enabled", "pantry.enabled", "relay.url",
                 "huggingface.co"):
        assert want in text, f"{OFFLINE} doesn't mention {want}"


def test_offline_mode_keeps_its_linked_anchor(built_site):  # noqa: F811
    """legacy/services/admin.md links #enabling-updates."""
    html = _read(built_site, "security", "offline-mode", "index.html")
    assert 'id="enabling-updates"' in html


def test_troubleshooting_starts_from_doctor_and_the_log():
    text = _text(TROUBLESHOOTING)
    for want in ("jarvisd doctor", "jarvisd doctor --fix", "logs/jarvisd.log", "journalctl -u jarvisd",
                 "jarvisd service status"):
        assert want in text, f"{TROUBLESHOOTING} doesn't mention {want}"
    for gone in ("docker compose", "~/.jarvis/compose", "./jarvis health"):
        assert gone not in text, f"{TROUBLESHOOTING} still has the Docker-era {gone}"


def test_docker_troubleshooting_kept_under_legacy():
    text = _text("legacy/troubleshooting.md")
    assert "docker compose" in text and "Port already in use" in text
