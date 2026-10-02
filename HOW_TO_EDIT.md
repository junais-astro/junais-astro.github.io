# Editing this website locally

## Everyday workflow

1. Edit files here in any editor (VS Code, etc.).
2. In a terminal, from this folder: `./publish.sh "what I changed"`
3. GitHub rebuilds the site in a few minutes (progress: the repo's **Actions** tab).

`publish.sh` first pulls anything GitHub committed (e.g. new papers), then commits and pushes your edits.

## Where things live

| What | File |
|---|---|
| About / home page text | `_pages/about.md` |
| CV | `_data/cv.yml` |
| News items | `_news/` (one file per item) |
| Projects | `_projects/` |
| Site settings (name, email, ORCID, ...) | `_config.yml` |
| Profile picture & images | `assets/img/` |
| Publications | **automatic** — don't edit `_bibliography/papers.bib` |

## Publications (automatic from ADS)

The list comes from the ADS public library
https://ui.adsabs.harvard.edu/public-libraries/rTaH98YmTs6-aZoxtV7WXg

- A GitHub Action (`.github/workflows/update-publications.yml`) checks the library **every day**
  and, if anything changed, rewrites `papers.bib` and rebuilds the site.
- To add or remove a paper: just add/remove it in the ADS library.
- To update immediately: GitHub → **Actions** → *update-publications* → **Run workflow**.
- Per-paper tweaks (selected, abbr badge, PDF link, hide a paper, ...): `_bibliography/extra_fields.yml`.

### One-time setup (ADS token)

1. Get a free token: https://ui.adsabs.harvard.edu/user/settings/token
2. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `ADS_TOKEN`
   - Value: the token
3. Optional, to run it locally too: `mkdir -p ~/.ads && echo YOUR_TOKEN > ~/.ads/dev_key`,
   then `python3 bin/update_publications.py` (or `./publish.sh --pubs`).

Note: GitHub pauses scheduled workflows after 60 days without any repository activity.
If that happens, clicking **Run workflow** (or any push) re-enables it.

## Optional: preview before publishing

With Docker Desktop installed: `docker compose up`, then open http://localhost:8080 (Ctrl+C to stop).
