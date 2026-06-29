"""Tests for the /blog section and the first post (roadmap#53).

This is the first test module in jarvis-docs. The repo ships no code, so the
meaningful proof of this docs feature is a clean ``mkdocs build --strict`` plus
assertions against the generated ``site/`` output, mirroring the engineering
breakdown's Verification checklist.

A single session-scoped fixture runs the documented build once into a temp dir
and yields the result + site path; every test asserts against that output.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROD_DOMAIN = "docs.jarvisautomation.dev"
STAGING_DOMAIN = "docs.jarvis.local"

POST_URL_SEGMENT = "llm-era-voice-assistant/"
POST_SRC = REPO_ROOT / "docs" / "blog" / "llm-era-voice-assistant.md"

# Internal annotations that must never reach the published page.
DRAFT_NOTE_NEEDLES = [
    "Draft notes",
    "remove before publishing",
    "r/selfhosted post title variants",
    "Cross-post timing",
]


@pytest.fixture(scope="session")
def built_site(tmp_path_factory):
    """Run ``mkdocs build --strict`` once; yield (CompletedProcess, site_dir)."""
    site_dir = tmp_path_factory.mktemp("site")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "-d", str(site_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    return result, site_dir


def _read(site_dir, *parts):
    return (site_dir.joinpath(*parts)).read_text(encoding="utf-8")


# --- Happy path -----------------------------------------------------------


def test_mkdocs_build_succeeds_strict(built_site):
    """The documented build command exits clean with the new pages wired in."""
    result, _ = built_site
    assert result.returncode == 0, (
        "mkdocs build --strict failed:\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    # No warning/missing-page complaints referencing the new blog pages.
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        low = line.lower()
        if "blog/" in low:
            assert "warning" not in low and "missing" not in low, (
                f"build complained about a blog page: {line}"
            )


def test_blog_index_renders_and_lists_post(built_site):
    """The listing page builds and links the first post with a real dek."""
    _, site_dir = built_site
    index = site_dir / "blog" / "index.html"
    assert index.exists(), "site/blog/index.html was not generated"
    html = index.read_text(encoding="utf-8")
    assert "Blog" in html
    assert f'href="{POST_URL_SEGMENT}"' in html, "index does not link the post"
    assert "Self-hosted voice assistants in the LLM era" in html
    # A real intro/dek, not an empty stub.
    assert "self-hosted voice" in html.lower()


def test_post_page_renders_body(built_site):
    """The post page builds with the full draft body (not the truncated excerpt)."""
    _, site_dir = built_site
    post = site_dir / "blog" / "llm-era-voice-assistant" / "index.html"
    assert post.exists(), "post page was not generated"
    html = post.read_text(encoding="utf-8")
    assert "Mycroft shut down in May 2023" in html
    assert "What Jarvis actually does" in html


def test_blog_in_top_nav(built_site):
    """`Blog` is reachable from the rendered top nav without displacing siblings."""
    _, site_dir = built_site
    home = _read(site_dir, "index.html")
    assert 'href="blog/"' in home, "no top-nav link to the blog section"
    assert "Blog" in home
    # Insertion between Troubleshooting and Reference left both siblings intact.
    assert "Troubleshooting" in home
    assert "Reference" in home


# --- Edge cases -----------------------------------------------------------


def test_canonical_and_sitemap_use_production_domain(built_site):
    """site_url resolves to the production domain in canonical + sitemap (SEO)."""
    _, site_dir = built_site
    post = _read(site_dir, "blog", "llm-era-voice-assistant", "index.html")
    assert PROD_DOMAIN in post
    assert STAGING_DOMAIN not in post
    sitemap = _read(site_dir, "sitemap.xml")
    assert PROD_DOMAIN in sitemap
    assert STAGING_DOMAIN not in sitemap


# --- Error / exception flows ----------------------------------------------


def test_post_strips_draft_notes(built_site):
    """Internal draft notes never reach the source or the published page."""
    _, site_dir = built_site
    src = POST_SRC.read_text(encoding="utf-8")
    rendered = _read(site_dir, "blog", "llm-era-voice-assistant", "index.html")
    for needle in DRAFT_NOTE_NEEDLES:
        assert needle not in src, f"source post still contains draft note: {needle!r}"
        assert needle not in rendered, f"rendered post leaks draft note: {needle!r}"
