#!/usr/bin/env bash
# Publish local edits to https://junais-astro.github.io
#
#   ./publish.sh                    apply website.yml, commit everything, push
#   ./publish.sh "Update CV"        same, with your own message
#   ./publish.sh --pubs "message"   also refresh publications from ADS first
#                                   (needs ADS_TOKEN or ~/.ads/dev_key locally)
#
# Or just double-click "Publish website.command" in Finder.
# GitHub rebuilds the site automatically after the push (takes a few minutes).
set -euo pipefail
cd "$(dirname "$0")"

# Use conda's git/python if available (the Apple git needs Xcode tools).
for d in "$HOME/anaconda3" "$HOME/miniconda3" "$HOME/miniforge3" "$HOME/opt/anaconda3" \
         "/opt/anaconda3" "/opt/miniconda3" "/opt/homebrew/anaconda3" "/opt/homebrew/Caskroom/miniconda/base"; do
  if [[ -x "$d/bin/git" ]]; then export PATH="$d/bin:$PATH"; break; fi
done

update_pubs=false
if [[ "${1:-}" == "--pubs" ]]; then update_pubs=true; shift; fi
msg="${1:-Update website}"

# The daily ADS job may have committed new papers on GitHub: get them first.
git pull --rebase --autostash

# Copy website.yml into the theme's files.
python3 bin/apply_website.py

if $update_pubs; then
  python3 bin/update_publications.py
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "Nothing to publish."
  exit 0
fi

echo
echo "Changes being published:"
git status --short
git add -A
git commit -q -m "$msg"
git push -q
echo
echo "Pushed. The site will be live in a few minutes:"
echo "  https://junais-astro.github.io"
echo "  (build progress: https://github.com/junais-astro/junais-astro.github.io/actions)"
