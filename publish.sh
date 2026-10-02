#!/usr/bin/env bash
# Publish local edits to https://junais-astro.github.io
#
#   ./publish.sh                    commit everything with a default message and push
#   ./publish.sh "Update CV"        same, with your own message
#   ./publish.sh --pubs "message"   also refresh publications from ADS first
#                                   (needs ADS_TOKEN or ~/.ads/dev_key locally)
#
# GitHub rebuilds the site automatically after the push (takes a few minutes).
set -euo pipefail
cd "$(dirname "$0")"

update_pubs=false
if [[ "${1:-}" == "--pubs" ]]; then update_pubs=true; shift; fi
msg="${1:-Update website}"

# The daily ADS job may have committed new papers on GitHub: get them first.
git pull --rebase --autostash

if $update_pubs; then
  python3 bin/update_publications.py
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "Nothing to publish."
  exit 0
fi

git status --short
git add -A
git commit -m "$msg"
git push
echo "Pushed. The site will be live in a few minutes:"
echo "  https://github.com/junais-astro/junais-astro.github.io/actions"
