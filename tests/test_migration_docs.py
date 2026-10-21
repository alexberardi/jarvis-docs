"""Tests for the migration guide from the old Docker install (loop item #381).

The installer site and the legacy banners link the guide, so it has a stable URL,
install/migrating-from-docker/, and the stub's old URL (install/migrate/) redirects to it.
The commands are checked against fixtures/jarvisd-usage.txt and the install scripts' option
blocks (fixtures/install-sh-options.txt, fixtures/install-ps1-options.txt).
"""

import re
from pathlib import Path

from test_site_structure import RELEASES, built_site  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
PAGE = "install/migrating-from-docker.md"
URL = "install/migrating-from-docker/"
LAUNCH_AGENTS = ["admin", "llm-proxy", "whisper-api", "tts", "ocr.service", "ocr.worker"]


def _text():
    return (DOCS / PAGE).read_text(encoding="utf-8")


def test_page_is_built_at_its_stable_url(built_site):
    assert (built_site / URL / "index.html").exists()


def test_old_stub_url_redirects_to_the_guide(built_site):
    html = (built_site / "install" / "migrate" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<meta http-equiv="refresh" content="0; url=([^"]+)">', html)
    assert m and m.group(1) == "../migrating-from-docker/", m


def test_legacy_banner_links_the_guide(built_site):
    html = (built_site / "legacy" / "index.html").read_text(encoding="utf-8")
    assert "/install/migrating-from-docker/" in html
    assert "/install/migrate/" not in html


def test_no_page_links_the_old_path():
    for md in DOCS.rglob("*.md"):
        assert "migrate.md" not in md.read_text(encoding="utf-8"), md


def test_guide_is_filled_and_says_pre_release():
    text = _text()
    assert "stub" not in text.lower() and "on its way" not in text
    assert "pre-release" in text.lower() and RELEASES in text
    assert "releases/latest" not in text
    assert "Jarvis Automation" in text


def test_start_fresh_path():
    text = _text()
    assert "docker compose down -v --rmi all" in text
    assert "rm -rf ~/.jarvis" in text
    for agent in LAUNCH_AGENTS:
        assert f"gui/$(id -u)/com.jarvis.{agent}" in text, agent
        assert f"~/Library/LaunchAgents/com.jarvis.{agent}.plist" in text, agent
    assert "setup-wizard.md" in text and ":7710/setup" in text


def test_keep_your_data_path():
    text = _text()
    usage = (FIXTURES / "jarvisd-usage.txt").read_text(encoding="utf-8")
    sh = (FIXTURES / "install-sh-options.txt").read_text(encoding="utf-8")
    ps1 = (FIXTURES / "install-ps1-options.txt").read_text(encoding="utf-8")
    for flag, source in [("--stop-legacy", sh), ("-StopLegacy", ps1)]:
        assert flag in source and flag in text, flag
    assert "jarvisd import-legacy --compose" in text and "import-legacy (--compose DIR" in usage
    assert "--apply" in text
    assert "jarvisd import-recipes" in text and "import-recipes [--apply]" in usage
    assert "docker start jarvis-postgres" in text
    # The import goes before the setup wizard; the CLI reference holds the flags.
    assert text.index("import-legacy --compose") < text.index("## Finish in the setup wizard")
    assert "../operate/cli.md#import-legacy" in text and "../operate/cli.md#import-recipes" in text


def test_node_version_table():
    text = _text()
    for band in ["0.1.0–0.1.3", "0.1.4–0.1.130", "0.1.131–0.1.149", "0.2.0", "0.3.1"]:
        assert f"| {band}" in text, band
    for internal in ["K2", "prod", "kitchen", "living room", "$BK", "Twilio", "Cloudflare"]:
        assert internal not in text, internal


def test_rollback_section():
    text = _text()
    assert "## Roll back" in text
    assert "launchctl bootstrap" in text and "docker update --restart" in text
