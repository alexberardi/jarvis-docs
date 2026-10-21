"""Tests for the site structure for jarvisd (loop item #377).

The docs switch to the jarvisd install ("Jarvis Automation", pre-release). The old
Docker/microservice docs move under a frozen Legacy section, every moved page keeps its
old URL as a redirect, and a few URLs that code and store listings link must keep
working: the privacy policy, the desktop agent page and its website-access anchor, the
Pantry rejection anchors, and the /app/* Universal Link files at the site root.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from test_pantry_rejections_docs import REASON_CODES

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
RELEASES = "https://github.com/alexberardi/jarvis-server/releases"

TOP_LEVEL = [
    "Home",
    "Install",
    "Use",
    "Models and hardware",
    "Operate",
    "Build",
    "Architecture",
    "Contributing",
    "Blog",
    "Legacy",
]

# Pages that move to the Legacy section (old path under docs/); services/* are all checked below.
LEGACY_PAGES = [
    "getting-started/index.md",  # the old install's overview; not in the issue's list
    "getting-started/installation.md",
    "getting-started/truenas.md",
    "reference/cli.md",
    "libraries/log-client.md",
    "libraries/config-client.md",
    "libraries/settings-client.md",
    "libraries/auth-client.md",
    "libraries/web-scraper.md",
    "services/index.md",
    "services/auth.md",
    "services/command-center.md",
    "services/config-service.md",
    "services/llm-proxy.md",
    "services/whisper-api.md",
    "services/tts.md",
    "services/installer.md",
]

INSTALL_STUBS = [
    "install/index.md",
    "install/requirements.md",
    "install/macos.md",
    "install/windows.md",
    "install/linux.md",
    "install/one-liners.md",
    "install/setup-wizard.md",
    "install/voice-node.md",
    "install/mobile-app.md",
    "install/upgrade.md",
    "install/uninstall.md",
    "install/migrate.md",
]


def _yaml_load(text):
    # mkdocs.yml carries !!python/name tags; a permissive loader is enough to read nav.
    class _Loader(yaml.SafeLoader):
        pass

    _Loader.add_multi_constructor("tag:yaml.org,2002:python/", lambda loader, suffix, node: None)
    return yaml.load(text, Loader=_Loader)


@pytest.fixture(scope="session")
def config():
    return _yaml_load((REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def redirects():
    return yaml.safe_load((REPO_ROOT / "redirects.yml").read_text(encoding="utf-8"))


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


def _url_dir(md_path):
    """docs path -> built directory (use_directory_urls): a/b.md -> a/b, a/index.md -> a."""
    p = Path(md_path).with_suffix("")
    return p.parent if p.name == "index" else p


def _nav_paths(entries):
    for entry in entries:
        if isinstance(entry, str):
            yield entry
        elif isinstance(entry, dict):
            for value in entry.values():
                if isinstance(value, str):
                    yield value
                else:
                    yield from _nav_paths(value)


def _section(nav, title):
    for entry in nav:
        if isinstance(entry, dict) and title in entry:
            return entry[title]
    raise AssertionError(f"no top-level {title!r} nav section")


# --- protected URLs -------------------------------------------------------


def test_privacy_policy_url_kept(built_site):
    assert (built_site / "security" / "privacy-policy" / "index.html").exists()


def test_desktop_agent_url_and_anchor_kept(built_site):
    html = _read(built_site, "clients", "desktop-agent", "index.html")
    assert 'id="turn-on-website-access"' in html


def test_pantry_rejection_anchors_kept(built_site):
    html = _read(built_site, "pantry", "rejections", "index.html")
    missing = [code for code in REASON_CODES if f'id="{code}"' not in html]
    assert not missing, f"rejection anchors missing: {missing}"


def test_root_files_are_in_the_built_site(built_site):
    """The build itself (not deploy.sh) puts the Universal Link files at the root."""
    aasa = built_site / ".well-known" / "apple-app-site-association"
    assert aasa.read_bytes() == (REPO_ROOT / ".well-known" / "apple-app-site-association").read_bytes()
    assert (built_site / "_headers").read_bytes() == (REPO_ROOT / "_headers").read_bytes()
    assert (built_site / "app-fallback" / "index.html").exists()
    rules = (built_site / "_redirects").read_text(encoding="utf-8").splitlines()
    assert "/app/*  /app-fallback/  200" in rules


def test_deploy_no_longer_copies_root_files():
    deploy = (REPO_ROOT / "deploy.sh").read_text(encoding="utf-8")
    assert "cp _redirects" not in deploy and "cp _headers" not in deploy


# --- name, repo, nav ------------------------------------------------------


def test_site_name_and_repo(config):
    assert config["site_name"] == "Jarvis Automation Docs"
    assert config["repo_url"].rstrip("/").endswith("alexberardi/jarvis-server")
    github = [s["link"] for s in config["extra"]["social"] if "github" in s["icon"]]
    assert github and all(link.rstrip("/").endswith("alexberardi/jarvis-server") for link in github)


def test_top_level_nav_order(config):
    titles = [next(iter(entry)) for entry in config["nav"]]
    assert titles == TOP_LEVEL


def test_nav_lists_every_page_once(config):
    paths = list(_nav_paths(config["nav"]))
    dupes = sorted({p for p in paths if paths.count(p) > 1})
    assert not dupes, f"listed twice in nav: {dupes}"
    on_disk = {
        p.relative_to(DOCS).as_posix()
        for p in DOCS.rglob("*.md")
        if not p.relative_to(DOCS).as_posix().startswith(("ops/", "overrides/"))
    }
    assert sorted(on_disk - set(paths)) == [], "pages missing from nav"


def test_install_section_has_the_pages(config):
    paths = set(_nav_paths(_section(config["nav"], "Install")))
    assert set(INSTALL_STUBS) <= paths
    assert "clients/desktop-agent.md" in paths


def test_build_section_has_commands_extending_and_pantry(config):
    paths = set(_nav_paths(_section(config["nav"], "Build")))
    assert {"commands/index.md", "extending/index.md", "extending/toolkit/index.md"} <= paths
    assert {"pantry/index.md", "pantry/rejections.md", "pantry/self-hosting.md"} <= paths


# --- install stubs ----------------------------------------------------------


def test_install_stubs_say_pre_release(built_site):
    for md in INSTALL_STUBS:
        text = (DOCS / md).read_text(encoding="utf-8")
        assert "pre-release" in text.lower(), f"{md} doesn't say it is a pre-release"
        assert RELEASES in text, f"{md} doesn't link the releases page"
        assert (built_site / _url_dir(md) / "index.html").exists()


def test_no_latest_download_links():
    """Only prereleases exist, so releases/latest/download/... 404s."""
    hits = [
        p.relative_to(DOCS).as_posix()
        for p in DOCS.rglob("*.md")
        if "jarvis-server/releases/latest" in p.read_text(encoding="utf-8")
    ]
    assert not hits, f"links to releases/latest: {hits}"


def test_setup_wizard_port(built_site):
    text = (DOCS / "install" / "setup-wizard.md").read_text(encoding="utf-8")
    assert ":7710/setup" in text


# --- legacy ---------------------------------------------------------------


def test_legacy_pages_moved(config):
    legacy = set(_nav_paths(_section(config["nav"], "Legacy")))
    for old in LEGACY_PAGES:
        assert not (DOCS / old).exists(), f"{old} still at its old path"
        assert f"legacy/{old}" in legacy, f"legacy/{old} not in the Legacy nav"


def test_every_legacy_page_has_banner_and_noindex(built_site):
    pages = sorted((DOCS / "legacy").rglob("*.md"))
    assert pages
    for md in pages:
        rel = md.relative_to(DOCS).as_posix()
        html = _read(built_site, *_url_dir(rel).parts, "index.html")
        assert '<meta name="robots" content="noindex">' in html, f"{rel} has no noindex"
        assert 'class="admonition warning legacy-banner"' in html, f"{rel} has no banner"
        assert "MinIO" in html and "install/" in html, f"{rel} banner text is wrong"


def test_current_pages_are_indexed(built_site):
    for parts in (("index.html",), ("install", "index.html"), ("clients", "desktop-agent", "index.html")):
        html = _read(built_site, *parts)
        assert 'content="noindex"' not in html
        assert "legacy-banner" not in html


# --- redirects ------------------------------------------------------------


def test_every_moved_page_redirects(redirects):
    for old in LEGACY_PAGES + ["services/" + p.name for p in (DOCS / "legacy" / "services").glob("*.md")]:
        assert redirects.get(old) == f"legacy/{old}", f"no redirect for {old}"


def test_redirect_pages_are_built(built_site, redirects):
    for old, new in redirects.items():
        assert not (DOCS / old).exists(), f"redirect source {old} is still a page"
        assert (DOCS / new).exists(), f"redirect target {new} is not a page"
        html = _read(built_site, *_url_dir(old).parts, "index.html")
        target = "/" + _url_dir(new).as_posix() + "/"
        m = re.search(r'<meta http-equiv="refresh" content="0; url=([^"]+)">', html)
        assert m, f"{old} has no meta refresh"
        resolved = (Path("/" + _url_dir(old).as_posix()) / m.group(1)).resolve().as_posix() + "/"
        assert resolved == target, f"{old} redirects to {resolved}, want {target}"
        assert f'<link rel="canonical" href="https://docs.jarvisautomation.dev{target}">' in html
