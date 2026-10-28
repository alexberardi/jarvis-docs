"""Tests for the security, architecture and privacy-policy audit fixes (issue #203, loop item #399).

Each claim is checked against jarvis-server main at 255467d (2026-10-21) unless noted:

- K2 passes through jarvisd's memory for desktop agents and headless nodes
  (internal/modules/cc/cc.go:375-377, settingsreq.go:255-354);
- the agent keeps K2 and command secrets in two 0600 JSON files
  (internal/agent/nodesettings/store.go:34);
- remote-LLM keys, the Twilio credentials and the HF token are settings in jarvis.db
  (llm/engine/config.go:126, 243; cc/phone/telephony.go:37-41), smart-home sign-ins are
  encrypted with <data dir>/cc-oauth.key (cc/smarthome_oauth.go:66);
- the agent updates itself by default (internal/agent/settings/settings.go:81);
- the push relay receives titles and bodies (notifications/push.go:442).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

AUTH = "architecture/authentication.md"
OVERVIEW = "architecture/index.md"
MODEL = "architecture/security.md"
VOICE = "architecture/voice-pipeline.md"
SECURITY = "security/index.md"
OFFLINE = "security/offline-mode.md"
ROADMAP = "security/compliance-roadmap.md"
PRIVACY = "security/privacy-policy.md"


def _text(rel):
    return (DOCS / rel).read_text(encoding="utf-8")


def _flat(rel):
    """The page with line breaks folded, so a phrase wrapped across lines still matches."""
    return " ".join(_text(rel).split())


# --- command secrets and K2 ---


def test_no_page_says_the_server_cannot_read_command_secrets():
    for rel in (AUTH, MODEL, SECURITY, PRIVACY):
        text = _flat(rel)
        for claim in ("cannot read them", "Not on the server at all", "never leaves the device"):
            assert claim not in text, f"{rel} still says {claim!r}"


def test_k2_passing_through_the_server_is_stated():
    for rel in (AUTH, MODEL, SECURITY):
        text = _flat(rel)
        assert "K2" in text, f"{rel} doesn't name K2"
        assert "through the server's memory" in text, f"{rel} doesn't say K2 passes through the server"


def test_agent_secret_files_are_0600_not_an_encrypted_database():
    for rel in (MODEL, PRIVACY):
        assert "0600" in _text(rel), f"{rel} doesn't say the agent's files are 0600"
    assert "SQLCipher" in _text(PRIVACY)


# --- what the server stores ---


def test_security_model_lists_the_third_party_secrets_the_server_holds():
    text = _text(MODEL)
    for want in ("remote_api_key", "Twilio", "llm.hf_token", "cc-oauth.key", "app-key"):
        assert want in text, f"{MODEL} doesn't list {want}"
    backups = [line for line in text.splitlines() if line.startswith("Backups")]
    assert backups and "Twilio" in backups[0], f"{MODEL}'s backup warning names only the signing key"


def test_windows_data_directory_is_named():
    for rel in (OVERVIEW, MODEL, SECURITY):
        assert r"%ProgramData%\jarvisd" in _text(rel), f"{rel} doesn't give the Windows data directory"
    assert "ACL" in _text(MODEL)


# --- egress and updates ---


def test_agent_self_update_is_on_by_default():
    for rel in (MODEL, OFFLINE):
        text = _text(rel)
        assert "auto_update" in text and "--no-auto-update" in text, f"{rel} doesn't name the agent's auto_update"
    assert "all off by default" not in _text(OFFLINE)


def test_python_engine_downloads_are_listed():
    for rel in (MODEL, OFFLINE):
        text = _text(rel)
        for want in ("PyPI", "uv"):
            assert want in text, f"{rel} doesn't list {want}"
    for want in ("llm.hf_endpoint", "llm.engine_base_url", "stt.engine_base_url"):
        assert want in _text(OFFLINE), f"{OFFLINE} doesn't name {want}"


def test_relay_is_opt_in_not_turned_on_by_the_wizard():
    for rel in (OVERVIEW, MODEL):
        assert "privacy step turns it on" not in _flat(rel), f"{rel} says the wizard turns the relay on"


# --- who sees what ---


def test_member_pages_are_listed():
    for rel in (AUTH, OVERVIEW):
        text = _flat(rel)
        assert "only Chat and Add-ons" not in text and "use Chat and Add-ons;" not in text
        for page in ("Inbox", "Workflows", "Recordings"):
            assert page in text, f"{rel} doesn't list the {page} member page"


def test_token_algorithm_and_cc_paths():
    text = _text(AUTH)
    assert "always RS256" not in text
    assert "auth.algorithm" in text
    for path in ("/cc/api/v0/nodes/register", "/cc/api/v0/node/mqtt-credentials"):
        assert path in text, f"{AUTH} doesn't give {path}"


def test_voice_settings_are_install_wide():
    # cc/household_settings.go's allowlist has no voice.* key; admin/bff.go refuses them per household.
    for rel in (VOICE, OVERVIEW):
        text = _flat(rel)
        assert "Household settings, in the web admin or the mobile app" not in text
        assert "household setting `voice." not in text, f"{rel} calls a voice.* key a household setting"
        assert "off by default per household" not in text
    assert "Privacy step" in _text(VOICE)


# --- compliance roadmap ---


def test_compliance_roadmap_is_about_jarvisd():
    text = _text(ROADMAP)
    for gone in ("Loki", "MinIO", "PostgreSQL", "Postgres", "Redis", "JARVIS_INFRA_BIND_HOST", "slowapi",
                 "setup-certs", "jarvis-auth", "HS256 to RS256", "jarvis/node/{", "Grafana", "SQLCipher"):
        assert gone not in text, f"{ROADMAP} still mentions {gone}"
    for want in ("RS256", "jarvis/nodes/", "X-Frame-Options", "jarvis.db", "Done", "Planned"):
        assert want in text, f"{ROADMAP} doesn't mention {want}"


# --- privacy policy ---


def test_privacy_policy_names_the_push_relay():
    text = _text(PRIVACY)
    assert "Push relay (optional)" in text
    for want in ("relay.jarvisautomation.io", "Expo", "titles and bodies"):
        assert want in text, f"{PRIVACY} doesn't mention {want}"
    assert "We do not operate any other cloud services that receive your data by default." not in text


def test_privacy_policy_describes_one_server_program():
    text = _text(PRIVACY)
    for gone in ("Whisper STT", "(Command Center)", "Jarvis Auth", "Whisper service", "backend services"):
        assert gone not in text, f"{PRIVACY} still says {gone}"
    assert "Jarvis Automation server" in text


def test_privacy_policy_date_bumped():
    assert "**Last updated:** October 28, 2026" in _text(PRIVACY)
