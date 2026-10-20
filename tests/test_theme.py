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
