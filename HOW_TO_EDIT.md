# Editing this website

## The two things you need

1. **`website.yml`** — the one file to edit: name, home-page text, address, news, CV,
   profile links, which pages show in the menu. Open it in any text editor.
2. **`Publish website.command`** — double-click it in Finder to put your changes online.
   (Terminal alternative: `bash publish.sh "what I changed"`.)

The site updates a few minutes later at https://junais-astro.github.io

Publishing copies `website.yml` into the theme's files (`_config.yml`, `_pages/about.md`,
`_news/`, `_data/cv.yml`, ...), so don't edit those by hand — your edits would be overwritten.

## Publications — fully automatic

They come from the ADS library
https://ui.adsabs.harvard.edu/public-libraries/rTaH98YmTs6-aZoxtV7WXg

- Add/remove a paper in ADS → the site updates the next morning (05:17 UTC).
- Update right now: GitHub repo → **Actions** → *update-publications* → **Run workflow**.
- Per-paper tweaks (selected, journal badge, PDF link, hide a paper): `_bibliography/extra_fields.yml`.
- Your name (as set in `name_in_papers` in `website.yml`) is printed in bold.

## Other files you may touch

| What | Where |
|---|---|
| Profile photo / images | `assets/img/` (photo file name is set in `website.yml`) |
| CV PDF | `assets/pdf/` (file name set in `website.yml`) |
| Anything else (theme, layout) | `_config.yml`, `_layouts/`, `_sass/` — rarely needed |

## If something goes wrong

- *"website.yml has a formatting problem near line N"*: usually indentation (use spaces,
  keep items lined up) or a value containing `: ` that needs "quotes". Fix and publish again.
- *"PyYAML is missing"*: run `conda install pyyaml` once.
- The ADS token is stored as the GitHub secret `ADS_TOKEN` (repo Settings → Secrets and
  variables → Actions). If you regenerate it on ADS, update it there.
- GitHub pauses the daily job after 60 days without repository activity; clicking
  **Run workflow** (or publishing anything) re-enables it.

## Optional: preview before publishing

With Docker Desktop installed: `docker compose up` in this folder, then open http://localhost:8080.
