"""Tests for the container install path (loop item #386).

jarvisd also runs as one container: the Unraid template (install/unraid.md, item #368) and plain
Docker or compose (install/docker.md). In a container jarvisd never replaces itself, so the
upgrade page says how a container is updated, and the migration guide has a container path:
a one-off `docker run --rm … import-legacy` with the Jarvis container stopped, never a
`docker exec` into the running one (import-legacy refuses while jarvisd answers on its port).

Names, ports and texts are from jarvis-server main: scripts/packaging/container/{Dockerfile,
entrypoint.sh}, scripts/packaging/unraid/jarvis.xml, internal/modules/admin/update.go
(ContainerHint) and .github/workflows/release.yml (every v* tag pushes :<version> and :latest,
pre-releases included; docs/decisions/2026-10-21-container-tags.md).
"""

import re
from pathlib import Path

from test_site_structure import built_site  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
IMAGE = "ghcr.io/alexberardi/jarvisd"

# internal/modules/admin/update.go ContainerHint, word for word.
HINT_UNRAID = (
    "This jarvisd runs in a container. Update it from Unraid's Docker tab: Check for Updates, "
    "then apply update. Your data in appdata is kept."
)
HINT_DOCKER = "This jarvisd runs in a container. Pull the new image and recreate the container; the /data volume is kept."


def _md(name):
    return (DOCS / "install" / name).read_text(encoding="utf-8")


def _html(site, *parts):
    return (site.joinpath(*parts)).read_text(encoding="utf-8")


def test_docker_page_is_built_and_in_nav(built_site):
    assert (built_site / "install" / "docker" / "index.html").exists()
    nav = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "install/docker.md" in nav
    assert nav.index("install/unraid.md") < nav.index("install/docker.md") < nav.index("install/one-liners.md")


def test_docker_page_has_run_and_compose_with_ports_volume_and_mode():
    text = _md("docker.md")
    assert "docker run" in text and "compose.yaml" in text
    for needle in (
        "7700:7700",
        "7710:7710",
        "1884:1884",
        ":/data",
        "JARVIS_CONTAINER=docker",
        "--restart=unless-stopped",
        "restart: unless-stopped",
        "PUID",
        "PGID",
        "--runtime=nvidia",
        "NVIDIA_VISIBLE_DEVICES=all",
        "Setup token:",
        "setup-token",
        f"{IMAGE}:",
    ):
        assert needle in text, f"docker page is missing {needle!r}"


def test_latest_is_published_for_every_release_and_the_template_default_is_used():
    # jarvis-server docs/decisions/2026-10-21-container-tags.md: every v* tag publishes :<tag> and
    # :latest, pre-releases included. The Unraid template's default :latest is what to use.
    unraid = _md("unraid.md")
    docker = _md("docker.md")
    upgrade = _md("upgrade.md")
    assert f"{IMAGE}:latest" in unraid and f"{IMAGE}:latest" in docker
    for name, text in (("unraid.md", unraid), ("docker.md", docker), ("upgrade.md", upgrade)):
        for stale in ("stable releases only", "No `:latest`", "no `:latest`", "Set **Repository** to a release tag",
                      "With a release tag in **Repository**", "names a release tag"):
            assert stale not in text, f"{name} still says {stale!r}"
    # The image only exists from rc18.4, the first release after rc18.
    assert "rc18" in unraid and "rc18" in docker
    assert 'id="the-image-tag"' in unraid or "### The image tag" in unraid


def test_port_conflicts_are_freed_not_remapped():
    # /services always hands out the container ports (7700 …), so a remapped host port breaks
    # discovery: a container mapped 27700→7700 still answers with http://<host>:7700/cc.
    unraid = _md("unraid.md")
    docker = _md("docker.md")
    trouble = unraid.split("a port is already in use", 1)[1].split("\n\n**", 1)[0]
    assert "host side" not in trouble and "/services" in trouble
    assert "change the left side" not in docker and "/services" in docker


def test_upgrade_page_has_container_section_with_both_hints():
    text = _md("upgrade.md")
    assert "## In a container" in text
    assert HINT_UNRAID in text
    assert HINT_DOCKER in text
    assert "docker compose pull" in text and "docker compose up -d" in text


def test_container_import_is_a_one_off_run_never_an_exec():
    text = _md("migrating-from-docker.md")
    assert "### On Unraid or in Docker" in text
    assert re.search(r"docker run --rm .*--network host", text)
    assert "import-legacy --from postgres://" in text
    assert "--apply" in text
    for line in text.splitlines():
        assert not ("docker exec" in line and "import-legacy" in line), line
    # The one-off run and the recipes step must run as the Jarvis container's own user: the
    # entrypoint re-owns /data to PUID:PGID (default 99:100) on every start.
    section = text.split("### On Unraid or in Docker", 1)[1].split("\n## ", 1)[0]
    assert "PUID" in section and "--user" in section


def test_container_pages_link_each_other(built_site):
    docker = _html(built_site, "install", "docker", "index.html")
    unraid = _html(built_site, "install", "unraid", "index.html")
    upgrade = _html(built_site, "install", "upgrade", "index.html")
    migrating = _html(built_site, "install", "migrating-from-docker", "index.html")
    assert 'id="in-a-container"' in upgrade
    assert 'id="on-unraid-or-in-docker"' in migrating
    for html in (docker, unraid):
        assert "../upgrade/#in-a-container" in html
        assert "../migrating-from-docker/#on-unraid-or-in-docker" in html
    assert "../docker/" in unraid and "../unraid/" in docker
    assert "../docker/" in upgrade and "../unraid/" in upgrade
