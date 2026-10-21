"""Tests for the Agent tab and the pages moved to Legacy (loop item #393).

The desktop agent's one page became a top-level Agent tab (docs/agent/), with the Raspberry Pi
Go node as a preview page. clients/desktop-agent/ stays as the Install section's short "Add a
computer" page, so the admin's link to its #turn-on-website-access anchor still lands on a
heading (a redirect page would drop the anchor). Node in Docker, the prompt provider pages, the
retired service libraries' index and the integration tests page moved under legacy/ with
redirects, and "Your First Command" moved from Operate to Build.
"""

import re

from test_site_structure import DOCS, _nav_paths, _read, _section, built_site, config, redirects  # noqa: F401

AGENT_PAGES = [
    "agent/index.md",
    "agent/pairing.md",
    "agent/macos-permissions.md",
    "agent/browser.md",
    "agent/voice.md",
    "agent/dictation.md",
    "agent/tools.md",
    "agent/updates-settings.md",
    "agent/troubleshooting.md",
    "agent/pi-node.md",
]

MOVED = {
    "clients/node-docker.md": "legacy/clients/node-docker.md",
    "extending/prompt-providers/index.md": "legacy/extending/prompt-providers/index.md",
    "extending/prompt-providers/reference.md": "legacy/extending/prompt-providers/reference.md",
    "contributing/integration-tests.md": "legacy/contributing/integration-tests.md",
}


def _article(html):
    start = html.index("<article")
    return html[start : html.index("</article>", start)]


def _current_pages():
    for p in DOCS.rglob("*.md"):
        rel = p.relative_to(DOCS).as_posix()
        if not rel.startswith(("legacy/", "ops/", "overrides/", "blog/")):
            yield rel, p.read_text(encoding="utf-8")


def test_agent_tab_follows_install_and_lists_its_pages(config):
    titles = [next(iter(entry)) for entry in config["nav"]]
    assert titles.index("Agent") == titles.index("Install") + 1
    assert list(_nav_paths(_section(config["nav"], "Agent"))) == AGENT_PAGES


def test_install_keeps_a_short_add_a_computer_entry(config):
    assert {"Add a computer": "clients/desktop-agent.md"} in _section(config["nav"], "Install")
    page = (DOCS / "clients" / "desktop-agent.md").read_text(encoding="utf-8")
    assert page.startswith("# Add a computer\n")
    assert "../agent/index.md" in page
    assert len(page.splitlines()) < 20, "the Install entry is a short pointer into the Agent tab"


def test_desktop_agent_anchor_points_at_the_steps(built_site):
    body = _article(_read(built_site, "clients", "desktop-agent", "index.html"))
    assert 'id="turn-on-website-access"' in body
    assert 'href="../../agent/browser/#turn-on-website-access"' in body
    assert 'id="turn-on-website-access"' in _read(built_site, "agent", "browser", "index.html")


def test_pi_node_is_marked_preview(built_site):
    body = _article(_read(built_site, "agent", "pi-node", "index.html"))
    assert "preview" in body.lower()
    assert "still the supported Pi node" in body
    assert "install-pi.sh" in body


def test_settings_page_says_auto_update_is_on_by_default():
    text = (DOCS / "agent" / "updates-settings.md").read_text(encoding="utf-8")
    # jarvis-server internal/agent/settings/settings.go:81 (auto_update, inverted --no-auto-update).
    assert re.search(r"^\| `auto_update` \| on \|", text, re.M)
    assert "Self-update is on by default" in text


def test_pairing_page_covers_the_mobile_app_and_the_admin():
    text = (DOCS / "agent" / "pairing.md").read_text(encoding="utf-8")
    for needle in ("**Add a computer**", "**Nodes**", "Pending pairings", "**Approve**", "Show a pairing code"):
        assert needle in text, needle


def test_moved_pages_redirect_to_legacy(redirects, built_site):
    for old, new in MOVED.items():
        assert redirects.get(old) == new, f"no redirect for {old}"
        assert not (DOCS / old).exists(), f"{old} is still a page"
        assert (DOCS / new).exists(), new
        stem = old[: -len(".md")]
        url = stem[: -len("index")] if stem.endswith("index") else stem + "/"
        html = _read(built_site, *url.strip("/").split("/"), "index.html")
        assert '<meta http-equiv="refresh"' in html, old
        assert "legacy/" in html, old


def test_moved_pages_are_in_the_legacy_nav(config):
    legacy = set(_nav_paths(_section(config["nav"], "Legacy")))
    assert set(MOVED.values()) | {"legacy/libraries/index.md"} <= legacy


def test_libraries_index_points_at_the_command_sdk():
    text = (DOCS / "libraries" / "index.md").read_text(encoding="utf-8")
    assert "(command-sdk.md)" in text
    assert "../legacy/libraries/index.md" in text
    assert "pip install" not in text


def test_no_current_page_links_a_moved_page():
    moved = ("node-docker.md", "integration-tests.md", "prompt-providers/")
    for rel, text in _current_pages():
        for link in re.findall(r"\]\(([^)\s]+)\)", text):
            if link.startswith(("http", "#")) or "legacy/" in link:
                continue
            for name in moved:
                assert name not in link, f"{rel} links the moved page {link}"


def test_first_command_is_under_build(config):
    assert "getting-started/first-command.md" in set(_nav_paths(_section(config["nav"], "Build")))
    assert "getting-started/first-command.md" not in set(_nav_paths(_section(config["nav"], "Operate")))
