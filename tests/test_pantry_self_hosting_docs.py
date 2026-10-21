"""The Pantry pages on jarvisd (#204 P1-P7).

On jarvisd the Pantry is chosen by the setting ``pantry.base_url`` (env fallback
``JARVIS_PANTRY_URL``) and is off per household until ``pantry.enabled`` is on
(jarvis-server internal/modules/cc/packages.go:41-63). ``command_store_url`` is
read only by the node-local CLI (jarvis-node-setup scripts/command_store.py).
The local compose file requires PANTRY_ADMIN_API_KEY
(jarvis-pantry docker-compose.local.yaml:37).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PANTRY = REPO_ROOT / "docs" / "pantry"


def _text(name):
    return (PANTRY / name).read_text(encoding="utf-8")


def test_self_hosting_uses_the_jarvisd_setting():
    page = _text("self-hosting.md")
    assert "command_store_url" not in page
    assert "`pantry.base_url`" in page
    assert "`JARVIS_PANTRY_URL`" in page


def test_pantry_pages_say_the_pantry_is_off_by_default():
    for name in ("index.md", "self-hosting.md"):
        page = _text(name)
        assert "`pantry.enabled`" in page, name
        assert "pantry_disabled" in page, name
        assert "../security/offline-mode.md" in page, name


def test_admin_key_is_required_in_the_quick_start():
    page = _text("self-hosting.md")
    quick_start = page.split("## Quick start", 1)[1].split("\n## ", 1)[0]
    assert "PANTRY_ADMIN_API_KEY" in quick_start.split("```", 2)[1], "not in the quick-start commands"
    assert "| `PANTRY_ADMIN_API_KEY` | required |" in quick_start
    assert "off until its variable is set" not in page


def test_pantry_pages_do_not_link_legacy():
    for page in PANTRY.glob("*.md"):
        assert "legacy/" not in page.read_text(encoding="utf-8"), page.name


def test_local_author_is_not_named_as_a_literal():
    # The stored author is "_local" (jarvis-pantry app/api/local_commands.py:25).
    assert "reserved `local` author" not in _text("self-hosting.md")


def test_pantry_base_url_is_server_wide_and_needs_no_restart():
    # pantry.base_url is not in cc's household allowlist (only pantry.enabled is,
    # jarvis-server internal/modules/cc/household_settings.go:67), and the admin
    # API refuses a household value (internal/admin/bff.go:313). It is read on every
    # call (cc/packages.go:89); JARVIS_PANTRY_URL is only the fallback while no
    # value is stored (internal/platform/settings/settings.go:53).
    page = _text("self-hosting.md")
    para = page.split("`pantry.base_url`", 1)[1].split("\n\n", 1)[0]
    assert "household can override" not in page
    assert "server-wide" in para
    assert "applies at once" in para
    assert "only while no value is set in Settings" in para
