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

echo "Deploying to Cloudflare Pages..."
npx wrangler pages deploy site --project-name=jarvis-docs --branch=main

echo "Done! Live at https://docs.jarvisautomation.dev"
