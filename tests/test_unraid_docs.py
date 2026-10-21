"""Tests for the Unraid install page and the single-port note (loop item #368, plan P4 piece 9).

jarvisd runs on Unraid as one container from a Community Applications template. These tests
pin the page that says how: it builds, it is in the Install nav, it names the three ports, the
appdata folder, the NVIDIA flags and the update path, and service discovery explains the one
API port and the legacy-ports switch.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGE = ("install", "unraid", "index.html")


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


def test_page_is_built_and_in_nav(built_site):
    assert built_site.joinpath(*PAGE).exists()
    assert "install/unraid.md" in (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def test_page_has_ports_data_gpu_and_updates(built_site):
    html = _read(built_site, *PAGE)
    for needle in (
        "7700",
        "7710",
        "1884",
        "/mnt/user/appdata/jarvis",
        "--runtime=nvidia",
        "NVIDIA_VISIBLE_DEVICES",
        "Check for Updates",
    ):
        assert needle in html, f"Unraid page is missing {needle!r}"


def test_service_discovery_explains_legacy_ports():
    text = (REPO_ROOT / "docs" / "architecture" / "service-discovery.md").read_text(encoding="utf-8")
    assert "server.legacy_ports" in text
