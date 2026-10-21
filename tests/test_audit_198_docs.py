"""Tests for the docs audit fixes (jarvis-docs #198, loop item #394).

Each test pins one audit finding against the code it was checked on (jarvis-server main
255467d / v0.1.0-rc18, jarvis-node-mobile main, jarvis-node-setup main, 2026-10-21):

- the setup wizard's steps are jarvis-server web/admin/src/components/wizard/steps.ts;
- the mobile app has no network discovery (jarvis-node-mobile
  src/services/configDiscoveryService.ts: "There is no network discovery"); only the desktop
  agent's first-run page browses mDNS (jarvis-server internal/agent/firstrun/mdns.go);
- built-in command names are jarvis-node-setup commands/*.py `command_name`.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

FIRST_COMMAND = "getting-started/first-command.md"
WHY = "getting-started/why-jarvis.md"


def _text(md):
    return (DOCS / md).read_text(encoding="utf-8")


def _current_pages():
    """Every page outside the frozen Legacy section and the blog (dated posts)."""
    for path in sorted(DOCS.rglob("*.md")):
        rel = path.relative_to(DOCS).as_posix()
        if rel.startswith(("legacy/", "blog/")):
            continue
        yield rel, path.read_text(encoding="utf-8")


@pytest.mark.parametrize("old", ["7711", "docker compose", "~/.jarvis", "ADMIN_API_KEY", "authorize_node",
                                 "localhost:7703", ":7702", "set_secret.py", "install_command.py"])
def test_first_command_is_for_jarvisd(old):
    assert old not in _text(FIRST_COMMAND), f"{FIRST_COMMAND} still describes the old stack: {old}"


def test_first_command_uses_jarvisd_tools_and_adds_nodes_from_the_app():
    text = _text(FIRST_COMMAND)
    for want in (":7710/admin/dashboard", "jarvisd service status", "jarvisd doctor", ":7700/health",
                 ":7700/services/health", ":7710/chat", "**Add Node**", "../install/voice-node.md",
                 "read-the-log"):
        assert want in text, f"{FIRST_COMMAND} doesn't mention {want}"


def test_why_jarvis_points_at_the_jarvisd_install():
    text = _text(WHY)
    assert "jarvis-admin" not in text and "install.sh" not in text, f"{WHY} still has the retired installer"
    assert "jarvis:install-cmd" not in text
    assert "../legacy/" not in text, f"{WHY} links to Legacy pages"
    for want in ("../install/index.md", "../install/setup-wizard.md", "Pi Zero 2 W"):
        assert want in text, f"{WHY} doesn't mention {want}"
    assert re.search(r"Pi Zero(?! 2)", text) is None, f"{WHY} names the Pi Zero, not the Pi Zero 2 W"


@pytest.mark.parametrize("md", ["install/requirements.md", "use/index.md"])
def test_no_placeholder(md):
    text = _text(md)
    assert "being written" not in text and "being rewritten" not in text, f"{md} is still a placeholder"


def test_requirements_names_systems_memory_and_disk():
    text = _text("install/requirements.md")
    for want in ("Apple silicon", "Intel Macs are not supported", "amd64", "arm64", "systemd", "### Memory",
                 "### Disk"):
        assert want in text, f"install/requirements.md doesn't mention {want}"


def test_use_landing_names_every_client():
    text = _text("use/index.md")
    for want in ("../install/voice-node.md", "../install/mobile-app.md", ":7710/chat", "../agent/index.md"):
        assert want in text, f"use/index.md doesn't point to {want}"


def test_setup_wizard_lists_the_five_model_steps():
    text = _text("install/setup-wizard.md")
    titles = ["Check", "Account", "Hardware", "Language model", "Speech-to-text", "Voice", "Voice recognition",
              "Memory & search", "Privacy", "This computer", "Done"]
    found = re.findall(r"^\d+\. \*\*([^*]+)\*\*", text, flags=re.M)
    assert found == titles, f"setup-wizard.md's steps are {found}, the wizard's are {titles}"
    assert "4. **Models**" not in text


def test_migration_page_names_the_model_steps():
    text = _text("install/migrating-from-docker.md")
    assert "then Models and Privacy" not in text
    assert "**Language model**" in text and "**Memory & search**" in text


# A sentence in which phones, the mobile app or nodes find the server (or its announcement)...
PHONE_FINDS = re.compile(
    r"\b(mobile app|phones?|nodes?)\b[^.\n]{0,60}?\b(finds?|discover\w*|looks? for)\b[^.\n]{0,40}?"
    r"\b(server|it|announcement)\b",
    re.I,
)
# ...on their own: by mDNS, or without being given the address.
ON_THEIR_OWN = re.compile(r"mDNS|by (themselves|itself)|on (their|its) own|without (typing )?an address", re.I)
NEGATION = re.compile(r"\b(never|doesn't|don't|does not|not)\b", re.I)


def _phone_discovery_claims(text):
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        if PHONE_FINDS.search(sentence) and ON_THEIR_OWN.search(sentence) and not NEGATION.search(sentence):
            yield sentence.strip()


def test_phone_discovery_check_catches_the_old_wording():
    old = [
        "| **5353** UDP | The server's mDNS announcement, so the mobile app finds it without typing an address. |",
        "The mobile app looks for that announcement, so on the same Wi-Fi it finds the server without an address.",
        "Phones and voice nodes connect to `http://<host>:7700`; they also find the server by themselves on your "
        "network.",
        "- Phones and nodes find the server by mDNS discovery.",
        "The mobile app finds the server over mDNS, checks `GET /info`, then reads `GET /services`.",
    ]
    for line in old:
        assert list(_phone_discovery_claims(line)), f"the check misses: {line}"


def test_no_page_says_phones_find_the_server_by_mdns():
    offenders = [f"{rel}: {s}" for rel, text in _current_pages() for s in _phone_discovery_claims(text)]
    assert not offenders, "pages say the mobile app or nodes find the server by themselves:\n" + "\n".join(offenders)
    trouble = _text("troubleshooting/index.md")
    assert "If the mobile app doesn't find the server by itself" not in trouble


def test_mdns_is_for_the_desktop_agent():
    network = _text("operate/network.md")
    assert "desktop agent" in network.split("## mDNS discovery")[1]
    assert "so the mobile app finds it" not in network


def test_home_page_command_names_exist():
    text = _text("index.md")
    assert "`tell_a_joke`" not in text and "`whats_up`" not in text
    assert "`tell_joke`" in text and "`check_alerts`" in text


def test_service_restart_uses_sudo():
    for md in ("operate/index.md", "operate/cli.md", "operate/network.md", "troubleshooting/index.md"):
        for line in _text(md).splitlines():
            if "jarvisd service restart" in line and "`jarvisd service start`" not in line:
                assert "sudo jarvisd service restart" in line, f"{md}: restart without sudo: {line.strip()}"


def test_doctor_lists_gpu_memory():
    for md in ("operate/cli.md", "troubleshooting/index.md"):
        assert "**gpu memory**" in _text(md), f"{md} doesn't list the gpu memory check"


def test_minor_fixes():
    assert "Pre-releases are not offered as updates" not in _text("install/unraid.md")
    one_liners = _text("install/one-liners.md")
    assert "The install scripts themselves are not in `SHA256SUMS`" not in one_liners
    assert "`install-pi.sh`" in one_liners
    models = _text("models/index.md")
    assert "MLX models first" in models and "informal" in models
    assert "informal" in _text("reference/benchmarks.md")
    ops = _text("ops/callback-signing-key-rotation.md")
    assert not ops.startswith("# Moved")
