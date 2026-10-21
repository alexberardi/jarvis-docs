"""The Contributing section describes how jarvis-server (jarvisd) is developed (#204 K1-K19).

Ground truth: jarvis-server's CLAUDE.md, README.md (build), go.mod, scripts/check,
scripts/contract.sh, scripts/e2e and .github/workflows/ci.yml. The old Python/Docker
workflow (./jarvis CLI, jarvis-log-client, per-service ports, jarvis-integration-tests)
appears only in the Python pointer sections or links to Legacy.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIB = REPO_ROOT / "docs" / "contributing"
PAGES = ["index.md", "coding-standards.md", "testing.md"]

# Old-stack terms that may appear only under a heading about the Python repos.
PYTHON_ONLY = ["jarvis-log-client", "jarvis_log_client", "JarvisLogger", "FastAPI"]
# Old-stack terms that must not appear at all.
RETIRED = ["./jarvis ", "jarvis-auth", "jarvis-config-service", "jarvis-command-center", ":7703", ":7704",
           ":7706", ":7707", "Piper", "Date context extraction", "Alembic", "docker compose"]


def _text(md):
    return (CONTRIB / md).read_text(encoding="utf-8")


def _sections(md):
    """Split a page into (heading, body) pairs at ## headings."""
    parts = re.split(r"^(#{2,3} .*)$", _text(md), flags=re.M)
    out = [("", parts[0])]
    out += list(zip(parts[1::2], parts[2::2]))
    return out


@pytest.mark.parametrize("md", PAGES)
def test_no_retired_workflow(md):
    text = _text(md)
    for term in RETIRED:
        assert term not in text, f"{md} still mentions {term!r}"


@pytest.mark.parametrize("md", PAGES)
def test_python_terms_only_in_python_sections(md):
    for heading, body in _sections(md):
        for term in PYTHON_ONLY:
            if term in body:
                assert "Python" in heading or "node" in heading.lower(), (
                    f"{md}: {term!r} appears under {heading!r}, not a Python section"
                )


def test_index_gives_the_jarvisd_workflow():
    text = _text("index.md")
    for want in ("scripts/fetch-sherpa-libs.sh", "make jarvisd", "go test -race ./...", "scripts/check",
                 "scripts/dev-run.sh", "scripts/sandbox", "CLAUDE.md", "docs/STATUS.md"):
        assert want in text, want
    assert "legacy/getting-started/installation.md" not in text
    assert "../install/index.md" in text


def test_coding_standards_cover_go_and_the_module_checklist():
    text = _text("coding-standards.md")
    for want in ("Go 1.27", "log/slog", "goose", "settings.Definition", "access tier", "scripts/check",
                 "line-length = 79", "line-length = 132"):
        assert want in text, want


def test_testing_documents_the_jarvisd_lanes():
    text = _text("testing.md")
    for want in ("go test -race", "scripts/check", "scripts/contract.sh", "scripts/e2e", "ci.yml",
                 "anthropic-live.yml", "transformers-live.yml", "go run ./tools/pipeline",
                 "../legacy/contributing/integration-tests.md"):
        assert want in text, want
