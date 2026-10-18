#!/usr/bin/env python3
"""Internal link checker for site/. Fails (exit 1) on any broken internal href/src.

Understands GitHub Pages project-root absolute paths (/openshelter/...).
Run after `python tools/build_site.py`; CI runs both automatically.
"""
import re, sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
EXTS = {".html",".xml",".svg",".png",".css",".js",".ico",".json",".woff2",".txt",".webp"}

def main() -> int:
    bad = []
    pages = list(SITE.rglob("*.html"))
    for pg in pages:
        txt = pg.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'(?:href|src)="([^"#]+)(?:#[^"]*)?"', txt):
            u = m.group(1)
            if u.startswith(("http://", "https://", "mailto:", "data:", "//")) or u == "":
                continue
            if u.startswith("/openshelter/"):      # GH Pages project root
                target = SITE / u[len("/openshelter/"):]
            elif u.startswith("/"):                 # domain root would 404 on project pages
                bad.append((str(pg.relative_to(SITE)), u, "domain-root path"))
                continue
            else:
                target = pg.parent / u
            target = Path(str(target).rstrip("/"))
            if target.suffix not in EXTS:
                cand = target / "index.html"
                target = target if target.exists() else cand
            if not target.exists():
                bad.append((str(pg.relative_to(SITE)), u, "missing"))
    print(f"checked {len(pages)} pages")
    for row in sorted(set(bad)):
        print("BROKEN:", *row)
    if bad:
        return 1
    print("0 broken internal links")
    return 0

if __name__ == "__main__":
    sys.exit(main())
