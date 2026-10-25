"""Tests for the client pages rewritten for jarvisd (loop item #380).

Voice nodes and the mobile app now talk to one server, jarvisd: one address (port 7700, found
over mDNS as _jarvis-config._tcp), the web app and setup wizard on 7710. These tests pin that the
client pages say so instead of listing the legacy microservices, that the Python node's install
line is on the current release, and that the Go Pi node (install-pi.sh) is offered only as an
experimental preview.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

NODE_SETUP_TAG = "v0.3.6"
SERVER_TAG = "v0.1.0-rc18.6"

CLIENT_PAGES = (
    "clients/index.md",
    "clients/node-setup.md",
    "clients/node-mobile.md",
)
ENTRY_PAGES = ("install/voice-node.md", "install/mobile-app.md")


def _read(rel):
    return (DOCS / rel).read_text(encoding="utf-8")


def test_python_node_install_line_is_on_the_current_release():
    page = _read("clients/node-setup.md")
    assert f"jarvis-node-setup/{NODE_SETUP_TAG}/install.sh | sudo bash" in page
    assert "v0.3.1" not in page


def test_go_pi_node_is_an_experimental_preview():
    url = f"https://github.com/alexberardi/jarvis-server/releases/download/{SERVER_TAG}/install-pi.sh"
    for rel in ("clients/node-setup.md", "install/voice-node.md"):
        page = _read(rel)
        assert "install-pi.sh" in page, rel
        assert re.search(r"experimental", page, re.IGNORECASE), rel
    node_setup = _read("clients/node-setup.md")
    assert url in node_setup
    # The Python node stays the supported one; the Go node installs disabled until --activate.
    assert "--activate" in node_setup
    assert "supported" in node_setup


def test_no_latest_download_links():
    # Every release so far is a prerelease, so releases/latest/download/... is a 404.
    for rel in CLIENT_PAGES + ENTRY_PAGES:
        assert "releases/latest/download" not in _read(rel), rel


def test_client_pages_point_at_one_jarvisd_server():
    for rel in CLIENT_PAGES:
        page = _read(rel)
        assert "jarvisd" in page, rel
        # The legacy TTS and notifications services are part of jarvisd now.
        assert "7707" not in page, rel
        assert "7712" not in page, rel
    for rel in ("clients/index.md", "clients/node-mobile.md"):
        page = _read(rel)
        assert "7703" not in page, rel
        assert "7700" in page, rel
    index = _read("clients/index.md")
    for needle in ("_jarvis-config._tcp", "7710", "architecture/index.md#ports", "legacy_ports"):
        assert needle in index, needle
    assert index.count("../agent/index.md") == 1
    # One API port: sign-in is found from 7700, not a port clients need.
    for rel in ("clients/index.md", "clients/node-mobile.md"):
        for line in _read(rel).splitlines():
            if line.startswith("|"):
                assert "7701" not in line, (rel, line)


def test_entry_pages_are_written():
    for rel in ENTRY_PAGES:
        page = _read(rel)
        assert "This page is a stub" not in page, rel
        assert "pre-release" in page, rel
        assert "https://github.com/alexberardi/jarvis-server/releases" in page, rel
