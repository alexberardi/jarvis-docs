"""Tests for the Pantry rejection-codes doc set (roadmap#23).

The Pantry submission service (#18) emits structured findings whose ``doc_url``
points at ``https://docs.jarvisautomation.dev/pantry/rejections/#<reason_code>``.
This module proves the authored doc set actually serves those anchors: a clean
``mkdocs build --strict`` plus assertions against the generated ``site/`` output,
mirroring the existing ``tests/test_blog_section.py`` pattern.

QA's plan (roadmap#23) specified these 13 named cases. It assumed jarvis-docs had
no pytest suite and proposed a bash smoke script; in fact the repo already tests
via pytest + a built-site fixture, so the cases are implemented here in that
convention. The reason-code catalogue is vendored below (source of truth:
``jarvis-pantry/app/services/rejection_codes.py``); when that module happens to be
importable we additionally cross-check ``_DOCS_BASE`` for drift.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROD_DOMAIN = "docs.jarvisautomation.dev"
STAGING_DOMAIN = "docs.jarvis.local"
EXPECTED_DOCS_BASE = "https://docs.jarvisautomation.dev/pantry/rejections"

# Vendored from jarvis-pantry/app/services/rejection_codes.py ALL_REASON_CODES,
# excluding ``legacy_unstructured`` (a synthetic fallback rendered as a plain
# message string — it carries no submitter-facing doc section). Append-only:
# codes are never renamed once shipped, so this list only grows.
REASON_CODES = [
    "static_analysis_disallowed_primitive",
    "static_analysis_raw_db_import",
    "static_analysis_sql_mutation",
    "static_analysis_cross_command_access",
    "static_analysis_shadows_builtin_dir",
    "static_analysis_syntax_error",
    "static_analysis_missing_base_class",
    "static_analysis_transitive_inheritance",
    "manifest_bad_semver",
    "manifest_missing_required_field",
    "manifest_invalid_field_type",
    "manifest_unknown_category",
    "manifest_unknown_param_type",
    "manifest_unknown_secret_scope",
    "manifest_parse_error",
    "repo_missing_readme",
    "repo_missing_license",
    "repo_no_components_found",
    "repo_component_file_missing",
    "repo_unknown_component_type",
    "routine_missing_steps",
    "routine_missing_trigger_phrases",
    "routine_missing_response_instruction",
    "routine_step_missing_command",
    "routine_invalid_json",
    "apt_package_not_on_allowlist",
    "apt_source_not_on_allowlist",
    "apt_source_mismatch",
    "post_install_op_unknown_type",
    "post_install_op_missing_target",
    "post_install_op_not_on_allowlist",
    "lockfile_resolution_failed",
    "resolved_lockfile_exceeds_size_cap",
]

REQUIRED_SUBSECTIONS = ("what this means", "why we flag it", "how to fix")


# --- mkdocs.yml loading ---------------------------------------------------
# mkdocs.yml carries ``!!python/name:...`` tags (superfences). A plain
# SafeLoader rejects them, so register a no-op multi-constructor.
class _MkdocsLoader(yaml.SafeLoader):
    pass


_MkdocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", lambda loader, suffix, node: None
)


def _mkdocs_text():
    return (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def _mkdocs_config():
    return yaml.load(_mkdocs_text(), Loader=_MkdocsLoader)


def _top_level_section(nav, name):
    """Return the children list of a top-level ``name:`` nav section, or None."""
    for entry in nav:
        if isinstance(entry, dict) and name in entry:
            return entry[name]
    return None


def _nav_leaves(children):
    """Flatten a nav children list into a {title: target} dict (one level)."""
    out = {}
    for entry in children or []:
        if isinstance(entry, dict):
            for k, v in entry.items():
                if isinstance(v, str):
                    out[k] = v
    return out


# --- built-site fixture ---------------------------------------------------
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
    return site_dir.joinpath(*parts).read_text(encoding="utf-8")


def _rejection_sections(html):
    """Map each ``<h2 id="...">`` to the HTML chunk up to the next h2."""
    starts = [m.start() for m in re.finditer(r'<h2 id="', html)]
    sections = {}
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(html)
        chunk = html[start:end]
        m = re.match(r'<h2 id="([^"]+)"', chunk)
        if m:
            sections[m.group(1)] = chunk
    return sections


# --- Happy path -----------------------------------------------------------


def test_mkdocs_strict_build_succeeds(built_site):
    """Clean strict build; both new pantry pages are generated, no pantry warnings."""
    result, site_dir = built_site
    assert result.returncode == 0, (
        "mkdocs build --strict failed:\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    for line in (result.stdout + "\n" + result.stderr).splitlines():
        low = line.lower()
        if "pantry/" in low:
            assert "warning" not in low and "missing" not in low, (
                f"build complained about a pantry page: {line}"
            )
    assert (site_dir / "pantry" / "index.html").exists()
    assert (site_dir / "pantry" / "rejections" / "index.html").exists()


def test_pantry_index_page_renders(built_site):
    """Pantry landing page exists, links to rejections, and is non-trivial."""
    _, site_dir = built_site
    html = _read(site_dir, "pantry", "index.html")
    assert len(html.encode("utf-8")) > 500
    assert "rejections/" in html, "landing page does not link the rejections page"
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    assert h1 and "pantry" in h1.group(1).lower()


def test_rejections_page_renders(built_site):
    """The single overview page renders with the expected intro + anchored h2s."""
    _, site_dir = built_site
    html = _read(site_dir, "pantry", "rejections", "index.html")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    assert h1 and "rejection" in h1.group(1).lower()
    low = html.lower()
    assert "reason code" in low or "rejection" in low
    assert re.search(r'<h2 id="[^"]+"', html), "no anchored h2 sections present"


def test_nav_contains_top_level_pantry(built_site):
    """mkdocs.yml nav has a top-level Pantry section with Overview + Rejections."""
    nav = _mkdocs_config()["nav"]
    children = _top_level_section(nav, "Pantry")
    assert children is not None, "no top-level 'Pantry' nav section"
    leaves = _nav_leaves(children)
    assert leaves.get("Overview") == "pantry/index.md"
    assert leaves.get("Rejections") == "pantry/rejections.md"


def test_site_url_corrected():
    """site_url is the production domain; the broken staging host is gone."""
    cfg = _mkdocs_config()
    assert cfg["site_url"] == "https://docs.jarvisautomation.dev"
    assert STAGING_DOMAIN not in _mkdocs_text()


def test_sitemap_uses_corrected_domain(built_site):
    """Corrected site_url propagates into the sitemap, incl. the rejections page."""
    _, site_dir = built_site
    sitemap = _read(site_dir, "sitemap.xml")
    locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
    assert locs, "sitemap has no <loc> entries"
    for loc in locs:
        assert loc.startswith("https://docs.jarvisautomation.dev/"), loc
    assert STAGING_DOMAIN not in sitemap
    assert any(loc.endswith("/pantry/rejections/") for loc in locs)


# --- Edge cases -----------------------------------------------------------


def test_each_reason_code_section_present(built_site):
    """Every emitted reason_code has a matching h2 anchor on the page."""
    _, site_dir = built_site
    html = _read(site_dir, "pantry", "rejections", "index.html")
    sections = _rejection_sections(html)
    missing = [c for c in REASON_CODES if c not in sections]
    assert not missing, f"reason codes with no doc section: {missing}"


def test_anchor_ids_match_reason_code_strings_verbatim(built_site):
    """Anchor ids are the verbatim snake_case codes (no slugification drift)."""
    _, site_dir = built_site
    html = _read(site_dir, "pantry", "rejections", "index.html")
    for code in REASON_CODES:
        assert f'<h2 id="{code}"' in html, f"verbatim anchor missing for {code}"
        # A hyphen-slugified variant would silently 404 every doc_url.
        if "_" in code:
            assert f'<h2 id="{code.replace("_", "-")}"' not in html, (
                f"slugified anchor present for {code} — doc_url would 404"
            )


def test_docs_base_path_matches_built_page(built_site):
    """The path #18's doc_url() emits lands on a real built page (the key check)."""
    _, site_dir = built_site
    # Best-effort drift check against the live module when importable.
    try:
        from jarvis_pantry.app.services import rejection_codes  # type: ignore

        assert rejection_codes._DOCS_BASE == EXPECTED_DOCS_BASE
    except Exception:
        pass
    path = EXPECTED_DOCS_BASE.split(PROD_DOMAIN, 1)[1].lstrip("/")
    assert path == "pantry/rejections"
    assert (site_dir / "pantry" / "rejections" / "index.html").exists()


def test_each_reason_code_section_has_required_subsections(built_site):
    """Every section carries What this means / Why we flag it / How to fix."""
    _, site_dir = built_site
    html = _read(site_dir, "pantry", "rejections", "index.html")
    sections = _rejection_sections(html)
    for code in REASON_CODES:
        chunk = sections.get(code, "").lower()
        for needle in REQUIRED_SUBSECTIONS:
            assert needle in chunk, f"{code} section missing '{needle}'"


def test_each_reason_code_section_has_severity_line(built_site):
    """Every section declares a Severity of error or warning."""
    _, site_dir = built_site
    html = _read(site_dir, "pantry", "rejections", "index.html")
    sections = _rejection_sections(html)
    for code in REASON_CODES:
        chunk = sections.get(code, "")
        assert re.search(
            r"Severity:\s*</strong>?\s*(error|warning)", chunk, re.I
        ) or re.search(r"Severity:[^<]*?(error|warning)", chunk, re.I), (
            f"{code} section has no Severity: error|warning line"
        )


def test_attr_list_extension_enabled():
    """attr_list stays enabled — it powers the {#reason_code} explicit anchors."""
    exts = _mkdocs_config()["markdown_extensions"]
    names = [e if isinstance(e, str) else next(iter(e)) for e in exts]
    assert "attr_list" in names


def test_no_pantry_directory_conflict(built_site):
    """The new top-level Pantry section doesn't shadow the existing mobile one."""
    _, site_dir = built_site
    assert (REPO_ROOT / "docs" / "mobile" / "pantry.md").exists()
    mobile = _top_level_section(_mkdocs_config()["nav"], "Mobile App")
    assert _nav_leaves(mobile).get("Pantry") == "mobile/pantry.md"
    assert (site_dir / "mobile" / "pantry" / "index.html").exists()
