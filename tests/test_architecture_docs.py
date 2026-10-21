"""Tests for the Architecture section for jarvisd (loop item #383).

The microservice-era architecture pages move to Legacy (old URLs keep working), and the
Architecture section describes jarvisd: an overview with one section per module in
jarvis-server's internal/modules, the voice pipeline, authentication and security.
"""

import re
from pathlib import Path

import yaml

from test_site_structure import _nav_paths, _section, _yaml_load

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

# jarvis-server internal/modules/, one package per module.
MODULES = ["admin", "auth", "cc", "config", "llm", "logs", "notifications", "ocr", "recipes", "stt", "tts"]

NEW_PAGES = [
    "architecture/index.md",
    "architecture/voice-pipeline.md",
    "architecture/authentication.md",
    "architecture/security.md",
]

# Old architecture pages: all move to legacy/architecture/. Those whose URL a new page
# reuses get no redirect; the others redirect to their legacy copy.
MOVED = ["index.md", "voice-pipeline.md", "service-discovery.md", "authentication.md", "cloud.md", "deployment.md"]
REDIRECTED = ["service-discovery.md", "cloud.md", "deployment.md"]

# The old per-service ports (7701-7712); jarvisd serves every module on 7700 by path.
# 7710 stays: it is jarvisd's admin port too.
OLD_PORT = re.compile(r":77(0[1-9]|1[12])\b")


def _config():
    return _yaml_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))


def _redirects():
    return yaml.safe_load((REPO_ROOT / "redirects.yml").read_text(encoding="utf-8"))


def _text(rel):
    return (DOCS / rel).read_text(encoding="utf-8")


def test_architecture_nav_has_the_new_pages():
    nav = list(_nav_paths(_section(_config()["nav"], "Architecture")))
    assert nav == NEW_PAGES


def test_overview_has_a_section_per_module():
    # Each module gets a heading that names its package, e.g. "### Command center (`cc`)".
    headings = re.findall(r"^### (.+)$", _text("architecture/index.md"), re.M)
    for module in MODULES:
        assert sum(f"(`{module}`)" in h for h in headings) == 1, f"no single ### heading for module {module}"


def test_new_pages_have_no_old_ports_or_microservices():
    for rel in NEW_PAGES + ["security/index.md"]:
        text = _text(rel)
        assert not OLD_PORT.search(text), f"{rel} names an old service port"
        assert "microservice" not in text.lower(), f"{rel} says microservice"


def test_new_pages_say_pre_release():
    assert "pre-release" in _text("architecture/index.md")


def test_old_pages_are_in_legacy_with_redirects():
    legacy = set(_nav_paths(_section(_config()["nav"], "Legacy")))
    redirects = _redirects()
    for name in MOVED:
        assert f"legacy/architecture/{name}" in legacy, f"legacy/architecture/{name} not in Legacy nav"
        assert (DOCS / "legacy" / "architecture" / name).exists()
    for name in REDIRECTED:
        assert redirects.get(f"architecture/{name}") == f"legacy/architecture/{name}"
    for name in set(MOVED) - set(REDIRECTED):
        # The new page owns this URL now; a redirect would overwrite it.
        assert f"architecture/{name}" not in redirects


def test_old_security_page_is_in_legacy():
    legacy = set(_nav_paths(_section(_config()["nav"], "Legacy")))
    assert "legacy/security/index.md" in legacy
    assert "security/index.md" not in _redirects()


def test_no_live_page_links_the_old_cloud_anchors():
    # The redirect page drops #anchors, so live pages link the Pantry page directly.
    for path in DOCS.rglob("*.md"):
        rel = path.relative_to(DOCS).as_posix()
        if rel.startswith("legacy/"):
            continue
        text = path.read_text(encoding="utf-8")
        assert "architecture/cloud.md" not in text, f"{rel} links architecture/cloud.md"
        assert "architecture/service-discovery.md" not in text.replace("legacy/architecture/", ""), (
            f"{rel} links the old service-discovery page"
        )


def test_provisioning_token_lifetime_matches_jarvisd():
    # jarvis-server internal/modules/cc/provisioning.go: provisioningTTL = 30 * time.Minute
    # (the legacy provisioning.py used 10).
    text = _text("architecture/authentication.md")
    assert "valid for 30 minutes" in text
    assert "valid for 10 minutes" not in text
