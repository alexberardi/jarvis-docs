"""Tests for the extending pages on jarvisd: agents, devices, providers, infrastructure (loop item #398).

The audit in jarvis-docs#202 found these pages written against the old stack: imports from
modules that don't exist (`stt_providers.base`, `device_managers.base`, ...), the abstract
`IJarvisSecret` used as a constructor, a `self.secret_service` nothing provides, a secret scope
("node") the SDK rejects, wrong provider names and media routes, `discover()` without `timeout`
(the node always passes it), and features jarvisd doesn't have (lightweight_chat, adapter and
tool-router training, go2rtc camera streaming, Piper). These tests pin the fixes on the
Markdown sources and the notes the built pages must carry.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTENDING = REPO_ROOT / "docs" / "extending"
PAGES = [
    "agents/index.md",
    "agents/alerts.md",
    "agents/scheduling.md",
    "devices/index.md",
    "devices/managers.md",
    "devices/protocols.md",
    "providers/index.md",
    "providers/stt.md",
    "providers/tts.md",
    "providers/wake-responses.md",
    "infrastructure/index.md",
    "infrastructure/jcc-client.md",
    "infrastructure/secrets.md",
    "infrastructure/datastore.md",
    "infrastructure/process.md",
    "infrastructure/settings.md",
]
PROVIDER_PAGES = [p for p in PAGES if p.startswith("providers/")]

# Each of these is wrong on jarvisd and the current node / SDK.
STALE = [
    "stt_providers.base",  # no such module: core.ijarvis_speech_to_text_provider
    "tts_providers.base",
    "wake_response_providers.base",
    "device_managers.base",  # packages import from jarvis_command_sdk
    "device_families.base import",
    "models.command_response",
    "JarvisCommandCenterClient()",  # its constructor needs base_url
    "self.secret_service",  # nothing provides it
    "IJarvisSecret(key=",  # abstract; JarvisSecret(key, description, scope, value_type)
    "jarvis_whisper",  # provider names are jarvis-whisper-api / jarvis-tts-api / static
    '"jarvis_tts',
    "static_wake",
    "/media/stt/transcribe",  # the route is /media/whisper/transcribe
    "/media/tts/synthesize",  # /media/tts/speak
    "generate-wake-response",  # POST /api/v0/wake-response
    "go2rtc",  # camera streaming is deferred on jarvisd
    "camera-credentials",
    "pysqlcipher3",  # the node uses sqlcipher3
    "jarvis pantry install",  # no such command
    "text_response(",  # not a CommandResponse constructor
    "get_all_protocols",  # get_all_families()
    "legacy/services/command-center.md",  # frozen legacy docs linked as current
]


def _text(page: str) -> str:
    return (EXTENDING / page).read_text(encoding="utf-8")


def _python_blocks(md: str) -> list[str]:
    return re.findall(r"^```python\n(.*?)^```", md, re.S | re.M)


@pytest.mark.parametrize("page", PAGES)
def test_no_stale_terms(page):
    text = _text(page)
    found = [term for term in STALE if term in text]
    assert not found, f"{page} still has {found}"


@pytest.mark.parametrize("page", PAGES)
def test_no_node_secret_scope(page):
    # The SDK accepts only "integration" and "user"; "node" raises ValueError.
    text = _text(page)
    assert not re.search(r'scope\s*=\s*"node"|, "node"[,)]|"scope": "node"', text), page


@pytest.mark.parametrize("page", PAGES)
def test_every_discover_call_passes_timeout(page):
    for block in _python_blocks(_text(page)):
        for call in re.findall(r"discover\(([^)]*)\)", block):
            assert "timeout" in call, f"{page}: discover({call}) without timeout"


def test_lightweight_chat_only_marked_as_missing_on_jarvisd():
    for page in PAGES:
        text = _text(page)
        if page == "infrastructure/jcc-client.md":
            continue
        assert "lightweight_chat" not in text, page
    jcc = _text("infrastructure/jcc-client.md")
    for para in jcc.split("\n\n"):
        if "lightweight_chat" in para or "train_tool_router" in para:
            assert "jarvisd doesn't have" in para and "cut from jarvisd" in para, para


def test_piper_only_as_cut():
    for page in PAGES:
        for line in _text(page).splitlines():
            if "Piper" in line:
                assert "Piper was cut" in line, f"{page}: {line}"


def test_jcc_client_is_built_on_the_sdk_helpers():
    text = _text("infrastructure/jcc-client.md")
    for needle in (
        "from jarvis_command_sdk import llm_chat_text",
        "from jarvis_command_sdk import cc_post",
        "/api/v0/node/llm/chat",
        "node-internal",
        "desktop agent",
    ):
        assert needle in text, needle
    assert "client = JarvisCommandCenterClient" not in text


@pytest.mark.parametrize("page", PROVIDER_PAGES)
def test_provider_pages_say_providers_are_not_packages(page):
    text = _text(page)
    assert "not package components" in text
    assert "Pantry" in text and "jdt" in text


def test_provider_names_and_routes_match_the_node():
    index = _text("providers/index.md")
    for name in ('"stt_provider": "jarvis-whisper-api"', '"tts_provider": "jarvis-tts-api"',
                 '"wake_response_provider": "jarvis-tts-api"'):
        assert name in index, name
    assert "/api/v0/media/whisper/transcribe" in _text("providers/stt.md")
    assert "/api/v0/media/tts/speak" in _text("providers/tts.md")
    wake = _text("providers/wake-responses.md")
    assert "POST /api/v0/wake-response" in wake
    assert '"static"' in wake
    for page in PROVIDER_PAGES:
        for block in _python_blocks(_text(page)):
            for imp in re.findall(r"^from (\S+) import", block, re.M):
                assert imp.split(".")[0] in {"abc", "dataclasses", "typing", "datetime", "core",
                                              "services", "os", "random", "subprocess", "tempfile",
                                              "requests"}, f"{page}: from {imp}"


def test_package_samples_import_from_the_sdk():
    # Agents, device managers and protocols ship in packages: the SDK is all a package can import.
    for page in ("agents/index.md", "agents/alerts.md", "devices/managers.md", "devices/protocols.md"):
        for block in _python_blocks(_text(page)):
            assert not re.search(r"^from (core|device_managers|device_families)\b", block, re.M), page


def test_secrets_page_documents_integration_and_user_scopes():
    text = _text("infrastructure/secrets.md")
    assert '`"integration"`' in text and '`"user"`' in text
    assert "JarvisStorage" in text


def test_agent_context_note_and_auto_disable():
    text = _text("agents/index.md")
    assert "custom agent context does not reach the LLM" in text
    assert "3 consecutive failures" in text
    assert "Agents" in text and "tab" in text


def test_camera_streaming_marked_not_on_jarvisd():
    text = _text("devices/protocols.md")
    assert "Not available on jarvisd" in text
    assert "Camera streaming is not available in this version" in text


def test_settings_page_is_cut_to_command_authors():
    text = _text("infrastructure/settings.md")
    assert "## For Command Authors" in text
    for gone in ("encrypt_snapshot(", "upload_snapshot(", "generate_dev_k2", "k2.key"):
        assert gone not in text, gone


def test_spotify_link_points_at_the_real_repo():
    text = _text("infrastructure/process.md")
    assert "github.com/alexberardi/jarvis-cmd-spotify" in text
    assert "github.com/jarvis-pantry/" not in text


@pytest.fixture(scope="module")
def built_site(tmp_path_factory):
    site_dir = tmp_path_factory.mktemp("site")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "-d", str(site_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    site_dir.joinpath(".build-log").write_text(result.stdout + result.stderr, encoding="utf-8")
    return site_dir


def _article(site_dir, *parts):
    html = site_dir.joinpath(*parts).read_text(encoding="utf-8")
    start = html.index("<article")
    return html[start : html.index("</article>", start)]


def test_no_broken_anchors_into_these_pages(built_site):
    # --strict only reports a missing anchor as INFO; links into these pages (including from
    # the frozen legacy pages) must still land.
    log = built_site.joinpath(".build-log").read_text(encoding="utf-8")
    broken = [
        line for line in log.splitlines()
        if "does not contain an anchor" in line and any(f"extending/{p}" in line for p in PAGES)
    ]
    assert not broken, broken


def test_built_pages_carry_the_notes(built_site):
    providers = _article(built_site, "extending", "providers", "index.html")
    assert "Providers are not package components" in providers
    assert "admonition" in providers
    jcc = _article(built_site, "extending", "infrastructure", "jcc-client", "index.html")
    assert "llm_chat_text" in jcc and "cc_post" in jcc
    protocols = _article(built_site, "extending", "devices", "protocols", "index.html")
    assert "must take <code>timeout</code>" in protocols
