"""Theme tests for the B · Quiet Violet direction (loop item #339).

The docs site follows jarvis-server's chosen direction B: system font stacks
(nothing is fetched), B's primary (#8A00C4 light, #c084fc dark) and neutral
greys for everything else. These tests pin the built site: the page loads no
web fonts, and the theme stylesheet defines B's primary for both colour
schemes.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


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


def _read(site_dir, *parts):
    return site_dir.joinpath(*parts).read_text(encoding="utf-8")


def test_index_loads_no_web_fonts(built_site):
    html = _read(built_site, "index.html")
    assert "fonts.googleapis.com" not in html
    assert "fonts.gstatic.com" not in html


def test_theme_css_serves_b_primary_for_both_schemes(built_site):
    css = _read(built_site, "assets", "stylesheets", "theme.css")
    light = css.split('[data-md-color-scheme="slate"]', 1)[0]
    dark = css.split('[data-md-color-scheme="slate"]', 1)[1]
    assert "#8A00C4" in light, "light scheme must use B's primary #8A00C4"
    assert "#c084fc" in dark, "dark scheme must use B's primary #c084fc"


def test_theme_css_sets_system_font_stacks(built_site):
    css = _read(built_site, "assets", "stylesheets", "theme.css")
    assert "system-ui" in css, "B uses the system font stack, no web font"
    assert "ui-monospace" in css, "B uses the system mono stack for code"


def _block(css, selector):
    """The CSS declaration block for a simple selector (first match)."""
    idx = css.find(selector + " {")
    assert idx != -1, f"{selector} missing from theme.css"
    start = css.find("{", idx)
    end = css.find("}", start)
    return css[start + 1 : end]


def test_type_scale_is_b(built_site):
    css = _read(built_site, "assets", "stylesheets", "theme.css")
    body = _block(css, ".md-typeset")
    assert "font-size: 15px" in body, "B body is 15px"
    assert "line-height: 1.55" in body, "B body line height is 1.55"
    h1 = _block(css, ".md-typeset h1")
    assert "font-size: 24px" in h1, "B title is 24px"
    assert "font-weight: 650" in h1, "B title weight is 650"
    h2 = _block(css, ".md-typeset h2")
    assert "font-size: 18px" in h2, "B heading is 18px"
    h3 = _block(css, ".md-typeset h3")
    assert "font-size: 15px" in h3, "B subheading is 15px"


def test_reduced_motion_keeps_colour_transitions(built_site):
    css = _read(built_site, "assets", "stylesheets", "theme.css")
    idx = css.find("@media (prefers-reduced-motion: reduce)")
    assert idx != -1, "B ships a prefers-reduced-motion block"
    start = css.find("{", idx)
    end = css.find("}", start)
    block = css[start:end]
    # Emil's rule: reduced motion removes movement, not colour and opacity changes.
    assert "transition-duration: 0.001ms" not in block, (
        "reduced motion must not kill the colour hovers"
    )
    assert "transition: none" in block, "reduced motion must stop the transform motion"


def test_header_and_tabs_sit_on_the_surface(built_site):
    # Material paints .md-header and .md-tabs with the primary; B wants neither to be a
    # violet slab. Both must sit on B's surface token in both schemes.
    css = _read(built_site, "assets", "stylesheets", "theme.css")
    light = css.split('[data-md-color-scheme="slate"]', 1)[0]
    dark = css.split('[data-md-color-scheme="slate"]', 1)[1]
    assert "--jb-surface: #ffffff" in light, "light surface is B's #ffffff"
    assert "--jb-surface: #1a1a20" in dark, "dark surface is B's #1a1a20"
    for selector in (".md-header", ".md-tabs"):
        body = _block(css, selector)
        assert "background-color: var(--jb-surface)" in body, (
            f"{selector} must sit on the surface, not the primary"
        )
        assert "primary" not in body.split("background-color:", 1)[1].split(";", 1)[0]
    tabs = _block(css, ".md-tabs")
    assert "border-bottom" in tabs, "the tabs bar has a hairline divider"
