#!/usr/bin/env python3
"""
Copy the contents of website.yml into the files the al-folio theme reads:

    _config.yml          name, e-mail, profile links, name to print in bold
    _pages/about.md      home page (subtitle, photo, address, bio, toggles)
    _news/*.md           news items          (this folder is fully managed here)
    _data/cv.yml         CV sections
    _pages/cv.md         CV PDF link
    _pages/*.md          which pages show in the menu

Run from anywhere:  python3 bin/apply_website.py      (publish.sh does it for you)
Only files whose content actually changes are rewritten.
"""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is missing: run  pip install pyyaml  (or conda install pyyaml)")

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "website.yml"

LINK_KEYS = {               # website.yml name -> _config.yml key
    "orcid": "orcid_id",
    "github": "github_username",
    "google_scholar": "scholar_userid",
    "linkedin": "linkedin_username",
    "twitter": "twitter_username",
    "researchgate": "research_gate_profile",
}
MENU_PAGES = {              # website.yml name -> file in _pages/
    "publications": "publications.md",
    "cv": "cv.md",
    "projects": "projects.md",
    "teaching": "teaching.md",
    "repositories": "repositories.md",
    "people": "profiles.md",
}

changed = []


# ---------------------------------------------------------------------------
def write_if_changed(path, text):
    old = path.read_text() if path.exists() else None
    if old != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        changed.append(str(path.relative_to(ROOT)))


def md_links(text):
    """[text](url) -> <a href='url'>text</a>  (for places that need HTML)"""
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r"<a href='\2'>\1</a>", str(text))


def yaml_scalar(v):
    if v is None or v == "":
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(json.dumps(str(x), ensure_ascii=False) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def set_key(text, key, value, indent=""):
    """Replace the first line `<indent>key: ...` keeping the file's other content."""
    pat = re.compile(rf"^{re.escape(indent)}{re.escape(key)}:.*$", re.M)
    if not pat.search(text):
        print(f"  warning: '{key}' not found, skipped")
        return text
    line = f"{indent}{key}: {yaml_scalar(value)}  # set in website.yml"
    return pat.sub(lambda m: line, text, count=1)


def set_front_matter_key(path, key, value):
    text = path.read_text()
    m = re.match(r"^---\n(.*?\n)---\n", text, re.S)
    if not m:
        return
    fm = m.group(1)
    pat = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    new_line = f"{key}: {yaml_scalar(value) if not isinstance(value, bool) else str(value).lower()}"
    fm = pat.sub(lambda _: new_line, fm, count=1) if pat.search(fm) else fm + new_line + "\n"
    write_if_changed(path, "---\n" + fm + "---\n" + text[m.end():])


# ---------------------------------------------------------------------------
def apply_config(w):
    path = ROOT / "_config.yml"
    text = path.read_text()
    text = set_key(text, "first_name", w.get("name"))
    text = set_key(text, "email", w.get("email"))
    for k, cfg_key in LINK_KEYS.items():
        text = set_key(text, cfg_key, (w.get("links") or {}).get(k))
    names = w.get("name_in_papers") or {}
    if names:
        # these two live inside the "scholar:" block (indented by 2 spaces)
        text = set_key(text, "last_name", names.get("last", []), indent="  ")
        text = set_key(text, "first_name", names.get("first", []), indent="  ")
    write_if_changed(path, text)


def apply_about(w):
    sub = [md_links(s) for s in (w.get("subtitle") or [])]
    subtitle = " <br /> ".join(sub) + " <br /> <hr>" if sub else ""
    fm = {
        "layout": "about",
        "title": "about",
        "permalink": "/",
        "subtitle": subtitle,
        "profile": {
            "align": "right",
            "image": w.get("photo") or None,
            "image_circular": bool(w.get("photo_round", False)),
        },
        "news": bool(w.get("show_news", False)),
        "latest_posts": False,
        "selected_papers": bool(w.get("show_selected_papers", False)),
        "social": bool(w.get("show_social_icons", False)),
    }
    address = w.get("address") or []
    if address:
        fm["profile"]["more_info"] = "".join(f"<p>{md_links(a)}</p>" for a in address)
    header = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=10000)
    body = (w.get("about") or "").strip() + "\n"
    write_if_changed(ROOT / "_pages" / "about.md",
                     "---\n# Generated from website.yml - edit that file instead.\n" + header + "---\n" + body)


def apply_news(w):
    folder = ROOT / "_news"
    wanted = {}
    for i, item in enumerate(w.get("news") or []):
        date = str(item.get("date", "")).strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            sys.exit(f"website.yml: news item {i + 1} needs a date like 2026-05-01 (got '{date}')")
        name = f"news_{date}_{i:02d}.md"
        wanted[name] = ("---\nlayout: post\n"
                        f"date: {date}\ninline: true\nrelated_posts: false\n---\n\n"
                        f"{str(item.get('text', '')).strip()}\n")
    for f in folder.glob("*.md"):
        if f.name not in wanted:
            f.unlink()
            changed.append(f"{f.relative_to(ROOT)} (removed)")
    for name, text in wanted.items():
        write_if_changed(folder / name, text)


def apply_cv(w):
    cv = w.get("cv") or []
    text = "# Generated from website.yml - edit that file instead.\n" + \
        yaml.safe_dump(cv, sort_keys=False, allow_unicode=True, width=10000)
    write_if_changed(ROOT / "_data" / "cv.yml", text)
    set_front_matter_key(ROOT / "_pages" / "cv.md", "cv_pdf", w.get("cv_pdf") or "")


def apply_menu(w):
    for key, show in (w.get("menu") or {}).items():
        if key not in MENU_PAGES:
            print(f"  warning: unknown menu entry '{key}' (known: {', '.join(MENU_PAGES)})")
            continue
        set_front_matter_key(ROOT / "_pages" / MENU_PAGES[key], "nav", bool(show))


# ---------------------------------------------------------------------------
def main():
    try:
        w = yaml.safe_load(SOURCE.read_text()) or {}
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" near line {mark.line + 1}" if mark else ""
        sys.exit(f"website.yml has a formatting problem{where}:\n{e}\n"
                 "(Check indentation, and put text containing ': ' in quotes.)")

    apply_config(w)
    apply_about(w)
    apply_news(w)
    apply_cv(w)
    apply_menu(w)

    if changed:
        print("Updated from website.yml:\n  " + "\n  ".join(changed))
    else:
        print("website.yml: nothing to change.")


if __name__ == "__main__":
    main()
