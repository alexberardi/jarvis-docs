"""Keep moved pages' old URLs working.

redirects.yml maps an old page to its new one (paths relative to docs/). For each entry
this writes a small page at the old URL that sends the browser on to the new one and names
the new one as canonical, so search engines move their index too. The build fails if a
target is not a page or if an old path is still a page.
"""

import html
import posixpath
from pathlib import Path

import yaml
from mkdocs.exceptions import PluginError

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Moved</title>
<meta http-equiv="refresh" content="0; url={rel}">
<link rel="canonical" href="{abs}">
<meta name="robots" content="noindex">
</head>
<body>
<p>This page moved to <a href="{rel}">{abs}</a>.</p>
</body>
</html>
"""


def _load(config):
    path = Path(config["config_file_path"]).parent / "redirects.yml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _url(page, use_directory_urls):
    """docs path -> site URL path without a leading slash ("a/b/" or "a/b.html")."""
    stem = page[: -len(".md")]
    if not use_directory_urls:
        return stem + ".html"
    if stem == "index" or stem.endswith("/index"):
        return stem[: -len("index")]
    return stem + "/"


def on_files(files, config, **kwargs):
    pages = {f.src_uri for f in files if f.src_uri.endswith(".md")}
    for old, new in _load(config).items():
        if old in pages:
            raise PluginError(f"redirects.yml: {old} is still a page; remove the page or the redirect")
        if new not in pages:
            raise PluginError(f"redirects.yml: {old} points at {new}, which is not a page")
    return files


def on_post_build(config, **kwargs):
    site = Path(config["site_dir"])
    site_url = (config.get("site_url") or "").rstrip("/")
    directory_urls = config["use_directory_urls"]
    for old, new in _load(config).items():
        old_url = _url(old, directory_urls)
        new_url = _url(new, directory_urls)
        dest = site / (old_url + "index.html" if directory_urls else old_url)
        base = posixpath.dirname(old_url.rstrip("/")) if not directory_urls else old_url.rstrip("/")
        rel = posixpath.relpath(new_url or ".", base or ".")
        if new_url.endswith("/") and not rel.endswith("/"):
            rel += "/"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            TEMPLATE.format(rel=html.escape(rel), abs=html.escape(f"{site_url}/{new_url}")),
            encoding="utf-8",
        )
