"""Copy the files the site serves outside MkDocs into the built site.

MkDocs skips dotfiles and only builds docs/, so these live at the repo root:

- .well-known/apple-app-site-association: Universal Links for the Jarvis mobile app
  (https://docs.jarvisautomation.dev/.well-known/apple-app-site-association).
- _headers: serves the AASA as JSON (Cloudflare Pages).
- _redirects: rewrites /app/* to the browser fallback when the app isn't installed.
- app-fallback/index.html: that fallback page.

Copying them in the build (not in deploy.sh) means `mkdocs build` alone gives the site
that ships, and the tests can check it.
"""

import shutil
from pathlib import Path

ROOT_FILES = [
    ".well-known/apple-app-site-association",
    "_headers",
    "_redirects",
    "app-fallback/index.html",
]


def on_post_build(config, **kwargs):
    repo = Path(config["config_file_path"]).parent
    site = Path(config["site_dir"])
    for name in ROOT_FILES:
        dest = site / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / name, dest)
