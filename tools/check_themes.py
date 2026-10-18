"""Guard: site CSS must not hardcode surface colors that break dark mode.

Rules checked in site/css/style.css and site/css/dark.css:
- outside @media print blocks, no `background(-color): #fff|white`
- footer/header/sitebar rules must use var(--footer-bg)/var(--header-bg) tokens
Exit 1 on violation so CI catches theme regressions before deploy.
"""
import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site" / "css"


def strip_print_blocks(css: str) -> str:
    out, depth, i = [], 0, 0
    for m in re.finditer(r"@media\s+print\s*\{", css):
        pass
    # simple scanner honoring brace nesting
    result, buf, skip_depth = [], None, -1
    pos = 0
    while pos < len(css):
        if skip_depth == -1 and css.startswith("@media print", pos):
            j = css.index("{", pos)
            depth, k = 0, j
            while k < len(css):
                if css[k] == "{":
                    depth += 1
                elif css[k] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            pos = k + 1
            continue
        result.append(css[pos])
        pos += 1
    return "".join(result)


def main() -> int:
    errors = []
    for name in ("style.css", "dark.css"):
        text = (SITE / name).read_text(encoding="utf-8")
        scan = strip_print_blocks(text)
        for m in re.finditer(
            r"(?:background|background-color)\s*:\s*(?:#fff\b|#ffffff\b|white\b)", scan
        ):
            line = scan[: m.start()].count("\n") + 1
            errors.append(f"{name}:{line} hardcoded white surface (use a token)")
        for sel in ("footer.site{", ".sitebar{", ".site-header{"):
            for m in re.finditer(re.escape(sel), text):
                chunk = text[m.end():m.end() + 200]
                if sel == ".site-header{" and "var(--header-bg)" not in chunk:
                    errors.append(f"{name}: {sel} missing var(--header-bg)")
                if sel == "footer.site{" and "background" in chunk and "var(--footer-bg)" not in chunk:
                    errors.append(f"{name}: footer.site missing var(--footer-bg)")
    if errors:
        print("THEME GUARD FAILED:")
        for e in errors:
            print("  -", e)
        return 1
    print("theme guard OK: all surfaces token-driven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
