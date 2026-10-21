"""Tests for the models and hardware pages (loop item #384).

The models page documents jarvis-server's model catalog (internal/modules/llm/models/catalog.json)
and which model to pick by hardware; the benchmarks page carries numbers measured on jarvisd with
scripts/toolbench, not the legacy command-center tables. These tests pin both: every language
model in the catalog is listed, both pages say Jarvis Automation is a pre-release, and the
benchmarks page no longer points at the legacy suite or its 0 % table.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS = ("models", "index.html")
BENCHMARKS = ("reference", "benchmarks", "index.html")
REQUIREMENTS = ("install", "requirements", "index.html")

# The catalog's `kind: llm` entries (jarvis-server main @ 507a55a), by `display` name. When the
# catalog gains or drops a language model, update this list and the models page together.
CATALOG_LLMS = (
    "Qwen 3 4B (Q4_K_M)",
    "Qwen 3 8B (Q4_K_M)",
    "Qwen 3.5 9B (Q4_K_M, vision)",
    "Qwen 3 14B (Q4_K_M)",
    "Qwen 3.8 27B (UD-Q4_K_M, vision)",
    "Qwen 3.5 9B (MLX 4-bit, Apple Silicon)",
    "Qwen 3.5 27B (MLX 4-bit, Apple Silicon)",
    "Qwen 3.5 35B-A3B (MLX 4-bit, Apple Silicon)",
)

# The other kinds, one display name each.
CATALOG_OTHERS = (
    "Whisper large-v3-turbo",
    "Whisper small.en",
    "Whisper base.en",
    "Kokoro v1.0",
    "all-MiniLM-L6-v2",
    "ERes2Net",
)


@pytest.fixture(scope="session")
def built_site(tmp_path_factory):
    site_dir = tmp_path_factory.mktemp("site")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "-d", str(site_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return site_dir


def _article(site_dir, *parts):
    # Only the page body: the nav and search index repeat other pages' titles.
    html = site_dir.joinpath(*parts).read_text(encoding="utf-8")
    m = re.search(r'<article class="md-content__inner[^"]*">(.*?)</article>', html, re.S)
    assert m, f"no article in {'/'.join(parts)}"
    return m.group(1)


def _text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def test_models_page_lists_every_catalog_llm(built_site):
    text = _text(_article(built_site, *MODELS))
    for name in CATALOG_LLMS + CATALOG_OTHERS:
        assert name in text, f"models page is missing {name!r}"
    assert "being written" not in text, "models page is still the stub"


def test_models_page_picks_by_hardware(built_site):
    text = _text(_article(built_site, *MODELS))
    for needle in ("16 GB", "98.8 %", "Mac mini M4", "llama.cpp", "MLX", "vLLM", "Transformers", "in progress", "Too big"):
        assert needle in text, f"models page is missing {needle!r}"


def test_benchmarks_page_is_measured_on_jarvisd(built_site):
    text = _text(_article(built_site, *BENCHMARKS))
    for gone in ("test_command_parsing.py", "docs/benchmarks/", "jarvis-node-setup"):
        assert gone not in text, f"benchmarks page still has legacy {gone!r}"
    # The legacy command-center table scored 0 %; "100 %" must not count as a hit.
    assert not re.search(r"(?<![\d.])0(\.0+)? ?%", text), "benchmarks page still has a 0 % result"
    for needle in ("scripts/toolbench", "bench_corpus.cc.yaml", "98.8 %", "Qwen 3 4B (Q4_K_M)", "2026-10-21"):
        assert needle in text, f"benchmarks page is missing {needle!r}"


@pytest.mark.parametrize("page", [MODELS, BENCHMARKS, REQUIREMENTS])
def test_pages_say_pre_release(built_site, page):
    text = _text(_article(built_site, *page))
    assert "pre-release" in text
    assert "rc18" in text


def test_requirements_links_the_models_page(built_site):
    html = _article(built_site, *REQUIREMENTS)
    assert 'href="../../models/"' in html
    assert "stub" not in _text(html)
