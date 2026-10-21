"""Tests for the extending docs audit (issue #201, loop item #397).

The extending index, discovery, where-code-runs and toolkit pages were written against the old
stack. On current main of the node and jdt: nothing watches the node's disk (a `jdt deploy` needs
a node restart), `validate_secrets()` returns the missing keys, installed packages land in
`custom_*` directories, jdt needs the SDK from git first, manifest `packages` entries are
objects, `jdt manifest` drops `targets` and other keys, and Pantry runs an AI security review
on top of the checks `jdt test` runs. These tests pin each correction in the page sources.
"""

import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs" / "extending"
TOOLKIT = DOCS / "toolkit"
SDK_GIT_INSTALL = "pip install git+https://github.com/alexberardi/jarvis-command-sdk.git"
JDT_GIT_INSTALL = "pip install git+https://github.com/alexberardi/jarvis-developer-toolkit.git"

PAGES = [
    DOCS / "index.md",
    DOCS / "discovery.md",
    DOCS / "where-code-runs.md",
    *(TOOLKIT / name for name in (
        "index.md", "init.md", "workflow.md", "test.md", "manifest.md", "deploy.md",
        "claude-code.md",
    )),
]


def _read(path):
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("page", PAGES, ids=lambda p: str(p.relative_to(DOCS)))
@pytest.mark.parametrize("stale", [
    "Drop a Python file",
    "background refresh thread",
    "background timer",
    "secret_service",
    "No restart needed",
    "No restart is required",
    "pushes a notification",
    "guarantees your package will pass review",
    "will pass Pantry validation",
    "it will pass review",
])
def test_stale_claims_are_gone(page, stale):
    assert stale not in _read(page)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: str(p.relative_to(DOCS)))
def test_no_bare_string_package_entries(page):
    # `packages` entries are {name, version} objects; a bare `- httpx` fails validation.
    assert not re.search(r"^\s*-\s+httpx\s*$", _read(page), re.M)


def test_index_drops_piper_and_the_command_center_box():
    text = _read(DOCS / "index.md")
    assert "Piper" not in text
    assert "Kokoro" in text
    assert 'subgraph CC ["Command Center' not in text
    assert "jarvisd" in text


def test_index_secrets_sample_uses_jarvis_secret():
    text = _read(DOCS / "index.md")
    assert "-> list[str]:\n    return [\"GOVEE_API_KEY\"]" not in text
    assert 'JarvisSecret("GOVEE_API_KEY"' in text
    assert "commands excepted" in text


def test_index_prompt_providers_not_auto_discovered():
    text = _read(DOCS / "index.md")
    assert "and prompt providers" not in text
    assert "not on jarvisd" in text


@pytest.mark.parametrize("page", [DOCS / "index.md", TOOLKIT / "index.md", TOOLKIT / "workflow.md"],
                         ids=lambda p: str(p.relative_to(DOCS)))
def test_sdk_git_install_comes_before_jdt(page):
    text = _read(page)
    assert SDK_GIT_INSTALL in text
    assert text.index(SDK_GIT_INSTALL) < text.index(JDT_GIT_INSTALL)


def test_discovery_samples_treat_validate_secrets_as_missing_list():
    text = _read(DOCS / "discovery.md")
    assert "if not instance.validate_secrets()" not in text
    assert "missing = instance.validate_secrets()" in text
    assert "plugins[instance.name]" not in text


def test_discovery_lists_install_dirs():
    text = _read(DOCS / "discovery.md")
    assert "## Where Installed Packages Land" in text
    for directory in (
        "commands/custom_commands/", "agents/custom_agents/", "device_families/custom_families/",
        "device_managers/custom_managers/", "routines/custom_routines/",
    ):
        assert directory in text


def test_discovery_prompt_provider_section_is_legacy():
    text = _read(DOCS / "discovery.md")
    assert "class PromptProviderFactory" not in text
    assert "| `PromptProviderFactory` |" not in text
    assert "Not supported on jarvisd" in text


def test_discovery_managers_are_inventory_backends():
    text = _read(DOCS / "discovery.md")
    assert "cloud API integrations for smart home devices" not in text
    assert "inventory backends" in text


def test_discovery_refresh_now_is_per_process():
    text = _read(DOCS / "discovery.md")
    assert "Start background refresh thread" not in text
    assert "does nothing to the running node" in text


@pytest.mark.parametrize("page", [TOOLKIT / "deploy.md", TOOLKIT / "workflow.md"],
                         ids=lambda p: str(p.relative_to(DOCS)))
def test_deploy_says_restart_the_node(page):
    text = _read(page)
    assert "sudo systemctl restart jarvis-node" in text
    # jdt's own success message is wrong; the page says so instead of repeating it.
    assert "Discovery caches will auto-refresh" in text


def test_deploy_ssh_runs_without_sudo():
    text = _read(TOOLKIT / "deploy.md")
    assert "install` with `sudo`" not in text
    assert "as the SSH user" in text
    assert "commands/custom_commands/<name>" in text


def test_workflow_has_no_docker_node_step():
    text = _read(TOOLKIT / "workflow.md")
    assert "Or to a Docker node" not in text
    assert "local, Docker, or SSH-accessible" not in text
    assert "The command center should route" not in text


def test_manifest_warns_that_jdt_manifest_drops_keys():
    text = _read(TOOLKIT / "manifest.md")
    assert "drops fields it does not know" in text
    for key in ("targets", "apt_packages", "apt_sources", "post_install", "jarvis_dependencies"):
        assert f"`{key}`" in text
    assert "  - name: httpx" in text


def test_where_code_runs_warns_about_jdt_manifest():
    text = _read(DOCS / "where-code-runs.md")
    assert "`jdt manifest` drops `targets`" in text


@pytest.mark.parametrize("page", [TOOLKIT / "index.md", TOOLKIT / "init.md"],
                         ids=lambda p: str(p.relative_to(DOCS)))
def test_prompt_provider_type_marked_legacy(page):
    assert "legacy only; not supported on jarvisd" in _read(page)


def test_toolkit_forbidden_imports_complete():
    assert "subprocess, os, shutil, ctypes, importlib" in _read(TOOLKIT / "index.md")


@pytest.mark.parametrize("page", [TOOLKIT / "index.md", TOOLKIT / "test.md", TOOLKIT / "workflow.md",
                                  TOOLKIT / "claude-code.md"],
                         ids=lambda p: str(p.relative_to(DOCS)))
def test_pantry_ai_review_mentioned(page):
    assert "AI security review" in _read(page)
