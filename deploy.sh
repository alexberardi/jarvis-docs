#!/usr/bin/env bash
# Deploy jarvis-docs to Cloudflare Pages
#
# First-time setup:
#   npx wrangler pages project create jarvis-docs --production-branch main
#
# Then configure custom domain in Cloudflare dashboard:
#   Pages > jarvis-docs > Custom domains > docs.jarvisautomation.dev
set -e
cd "$(dirname "$0")"

pip install -q -r requirements.txt 2>/dev/null
echo "Building docs..."
mkdocs build

# Inject the Apple App Site Association + headers into the build output.
# MkDocs skips dotfiles, so these live at the repo root and are copied into
# site/ here. Serves https://docs.jarvisautomation.dev/.well-known/apple-app-site-association
# (Universal Links for the Jarvis mobile app's Control Center button).
echo "Injecting Apple App Site Association..."
mkdir -p site/.well-known
cp .well-known/apple-app-site-association site/.well-known/apple-app-site-association
cp _headers site/_headers

echo "Deploying to Cloudflare Pages..."
npx wrangler pages deploy site --project-name=jarvis-docs --branch=main

echo "Done! Live at https://docs.jarvisautomation.dev"
