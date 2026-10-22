"""Tests for the clients, mobile app and libraries audit fixes (issue #199, loop item #395).

The audit checked these pages against current main of jarvis-node-setup, jarvis-node-mobile,
jarvis-command-sdk and jarvis-server. These tests pin the fixes: no old-stack ports, CLIs or APIs
that do not exist, the mobile pages describe the app's real screens and strings, the command SDK
page lists the real abstract interface, and node-setup puts the user install before developer
material.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

AUDITED_DIRS = ("clients", "mobile")

# Strings the audit found that name things that do not exist (or old-stack ports and copy).
GONE = (
    ":7703",
    "suppress_wake_for",
    "wake-gate-extended",
    "jarvis pantry install",
    "AI Builder",
    "Import from Clipboard",
    "Sign In",
    "14 days",
    "Configure devices",
    "3+ required",
    "Back Up Encryption Key",
    "QR code scanning to pair",
    "QR code and Wi-Fi",
    "Email + password or another attempt",
    "`command_center_url`",
    "ADMIN_API_KEY>",
    "restarts its service",
    "5 minutes without the server",
)


def _read(rel):
    return (DOCS / rel).read_text(encoding="utf-8")


def _pages():
    for d in AUDITED_DIRS:
        yield from sorted((DOCS / d).glob("*.md"))


def test_gone_strings_are_not_in_clients_or_mobile():
    for path in _pages():
        text = path.read_text(encoding="utf-8")
        for needle in GONE:
            assert needle not in text, (path.relative_to(DOCS).as_posix(), needle)


def test_routines_page_matches_the_app():
    page = _read("mobile/routines.md")
    assert "Scheduled errands" in page
    assert re.search(r"play|run button", page, re.IGNORECASE)
    assert "at least one trigger phrase" in page
    for label in ("Create Routine", "Commands from", "At a time", "Repeating", "Run on"):
        assert label in page, label
    assert "Export" not in page


def test_pantry_page_matches_the_app():
    page = _read("mobile/pantry.md")
    for label in ("Popular", "Newest", "A-Z", "Bundle", "Install to Command Center", "Test Install"):
        assert label in page, label
    # Only admins and power users see the Install button.
    assert re.search(r"admin", page, re.IGNORECASE) and re.search(r"power user", page, re.IGNORECASE)
    # There is no Routine package type.
    assert "| Routine |" not in page
    # The install button's label depends on the nodes' versions: Install (none have it),
    # Update to v... (every node has an older version), Install / Update to v... (mixed),
    # and Up to date (v...) when all nodes are current.
    assert "**Update to v…" in page
    assert "**Install / Update to v…" in page
    assert "Up to date (v" in page
    # The Root-privileged install confirmation comes before node selection.
    assert page.index("Root-privileged install") < page.index("Select nodes")


def test_auth_page_matches_the_server_and_app():
    page = _read("mobile/auth.md")
    assert "30 days" in page
    assert "invite code" in page.lower()
    assert "Set Server URL" in page
    assert "Log In" in page
    assert "Registration is closed" in page
    assert "temporary password" in page.lower()
    assert "username" not in page.lower()


def test_settings_page_joins_with_an_invite_code():
    page = _read("mobile/settings.md")
    assert "Invite Code" in page
    assert "Config Service URL" in page
    assert "Delete Account" in page
    assert "Enter a server URL and create an account" not in page


def test_mobile_index_header_and_nodes_tab():
    page = _read("mobile/index.md")
    assert "Jarvis Automation app" in page
    assert "New conversation" in page
    assert "Add a computer" in page
    nodes = _read("mobile/nodes.md")
    for label in ("Prepare", "Connect to Node", "Backup Encryption Key", "Add a computer"):
        assert label in nodes, label


def test_no_old_service_names_in_mobile_pages():
    for path in sorted((DOCS / "mobile").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for needle in ("command center", "Whisper service", "TTS service"):
            assert needle not in text, (path.name, needle)


def test_command_sdk_page_lists_the_real_interface():
    page = _read("libraries/command-sdk.md")
    for needle in (
        "generate_prompt_examples",
        "generate_adapter_examples",
        "keywords",
        "required_secrets",
        "run(self, request_info",
    ):
        assert needle in page, needle
    for kind in ('"text"', '"float"', '"duration"', '"object"'):
        assert kind in page, kind
    changelog = page.split("## Changelog", 1)[1]
    for version in ("0.6.0", "0.10.0", "0.13.0"):
        assert f"| {version} |" in changelog, version
    assert "get_stream_source--camera" not in page


def test_provisioning_endpoint_table_has_three_columns():
    page = _read("clients/provisioning.md")
    lines = page.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Path |"))
    table = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        table.append(line)
    assert len(table) > 2
    for line in table:
        assert line.strip().strip("|").count("|") == 2, line
    assert "Prepare" in page and "Connect to Node" in page


def test_node_setup_puts_the_user_install_before_developer_material():
    page = _read("clients/node-setup.md")
    headings = [line for line in page.splitlines() if line.startswith("## ")]
    names = [h[3:] for h in headings]
    assert names[0] == "Quick Install"
    # Configuration and troubleshooting come before the developer section.
    dev = next(i for i, n in enumerate(names) if n.startswith("For developers"))
    assert any(n.startswith("Configuration") for n in names[:dev])
    assert any(n.startswith("Troubleshooting") for n in names[:dev])
    # Old-stack material is gone.
    for needle in ("jarvis-command-center", "/root/.jarvis", "../legacy/services/command-center.md"):
        assert needle not in page, needle
    # The real wake gate, command-store CLI and config keys.
    for needle in (
        "core/voice_filters.py",
        "not_for_me_escalated_quiet_seconds",
        "scripts/command_store.py install",
        "jarvis_config_service_url",
        "jarvis_command_center_api_url",
        "ghcr.io/alexberardi/jarvis-node-audio",
        "http://<server>:7700/cc",
    ):
        assert needle in page, needle
