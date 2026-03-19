#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
pip install -q -r requirements.txt 2>/dev/null
mkdocs serve -a 0.0.0.0:7730
