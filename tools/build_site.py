#!/usr/bin/env python3
"""OpenShelter static site builder, multi-page, shared layout, one source of truth.

Generates: index (home), how/, trust/, briefs/ (+gallery), mission/, contribute/,
docs/ (redirects to repo). Rebuild with:  python tools/build_site.py
All pages share header/nav/footer via the LAYOUT template; content lives in
CONTENT dict below so copy edits never touch HTML boilerplate again.
"""
from __future__ import annotations
import json, os, re, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

# ---------------------------------------------------------------- shared chrome
# Header shows ONLY what a visitor needs at decision height (5 tabs + CTA).
# Everything else lives in the footer navigation below.
NAV = [
    ("How it works", "/how/"),
    ("Live demo", "/demo/"),
    ("Example plans", "/briefs/"),
    ("Trust & data", "/trust/"),
    ("Newsroom", "/news/"),
]
CTA_NAV = ("Get involved", "/contribute/")  # rendered as the header action button
FOOTER_EXTRA = [  # secondary pages reachable from the footer only
    ("Home", "index.html"),
    ("Mission", "mission/"),
    ("Contribute", "contribute/"),
    ("GitHub", REPO := "https://github.com/Manyaai/openshelter"),
    ("Report an issue", REPO + "/issues/new"),
]
ACTIVE_KEY = {  # page id -> nav label that should be marked active
    "home": None, "how": "How it works", "demo": "Live demo",
    "briefs": "Example plans", "trust": "Trust & data", "news": "Newsroom",
    "mission": None, "contribute": None,
}
# pager order for prev/next navigation cards at the bottom of sub-pages
PAGER_ORDER = ["how", "demo", "briefs", "trust", "news", "mission", "contribute"]
PAGER_HREF = {"how": "how/", "demo": "demo/", "briefs": "briefs/", "trust": "trust/",
              "news": "news/", "mission": "mission/", "contribute": "contribute/"}
PAGER_TITLE = {"how": "How it works", "demo": "Live demo", "briefs": "Example plans",
               "trust": "Trust & data", "news": "Newsroom", "mission": "Mission",
               "contribute": "Get involved"}

def rel(prefix: str, path: str) -> str:
    """Resolve an absolute site path relative to a page directory prefix."""
    if prefix == "":
        return "." + path if not path.startswith(".") else path
    depth = prefix.rstrip("/").count("/") + 1
    return "../" * depth + path.lstrip("./")

# Footer carries the full site map: primary pages (matching header labels)
# plus secondary pages only reachable here. No badge images, no duplicates.
# Standard three-column footer: brand block + two navigation groups.
# Everything a visitor might want but doesn't need at header height lives here.
FOOTER_COLS = """
  <div class="f-grid">
    <div class="f-brand">
      <a class="f-name" href="{URL}index.html">OpenShelter</a>
      <p class="f-tag">Free, open-source tool that turns public hazard data and building codes into plain-language shelter design briefs.</p>
      <p class="f-meta">AGPL-3.0 licensed · Built with open data (USGS, NOAA)</p>
    </div>
    <nav class="f-col" aria-label="Explore">
      <h4>Explore</h4>
      <a href="{URL}how/">How it works</a>
      <a href="{URL}demo/">Live demo</a>
      <a href="{URL}briefs/">Example plans</a>
      <a href="{URL}trust/">Trust &amp; data</a>
    </nav>
    <nav class="f-col" aria-label="Project">
      <h4>Project</h4>
      <a href="{URL}mission/">Mission</a>
      <a href="{URL}news/">Newsroom</a>
      <a href="{URL}contribute/">Get involved</a>
      <a href="https://github.com/Manyaai/openshelter">GitHub</a>
      <a href="https://github.com/Manyaai/openshelter/issues/new">Report an issue</a>
    </nav>
  </div>
"""

REPO = "https://github.com/Manyaai/openshelter"

def crumbs(page_id: str, p: str) -> str:
    """Breadcrumb trail for sub-pages (Home / <current section>)."""
    if page_id == "home":
        return ""
    label = PAGER_TITLE.get(page_id, page_id.title())
    return (f'<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap">'
            f'<a href="{p}index.html">Home</a><span aria-hidden="true">/</span>'
            f'<span aria-current="page">{label}</span></div></nav>')


def pager(page_id: str, p: str) -> str:
    """Previous / next navigation cards at the bottom of every sub-page."""
    if page_id == "home" or page_id not in PAGER_ORDER:
        return ""
    i = PAGER_ORDER.index(page_id)
    prev_id = PAGER_ORDER[i - 1] if i > 0 else None
    next_id = PAGER_ORDER[i + 1] if i + 1 < len(PAGER_ORDER) else None
    cells = []
    if prev_id:
        cells.append(f'<a class="pg prev" href="{p}{PAGER_HREF[prev_id]}"><small>&larr; Previous</small><b>{PAGER_TITLE[prev_id]}</b></a>')
    else:
        cells.append(f'<a class="pg prev" href="{p}index.html"><small>&larr; Start from</small><b>Home</b></a>')
    if next_id:
        cells.append(f'<a class="pg next" href="{p}{PAGER_HREF[next_id]}"><small>Next &rarr;</small><b>{PAGER_TITLE[next_id]}</b></a>')
    else:
        cells.append(f'<a class="pg next" href="{REPO}"><small>See the code</small><b>GitHub</b></a>')
    return f'<nav class="pager" aria-label="Page navigation"><div class="wrap grid grid-2">{"".join(cells)}</div></nav>'


def layout(page_id: str, title: str, desc: str, prefix: str, body: str,
           canonical: str, extra_head: str = "", scripts: str = "") -> str:
    p = prefix  # e.g. "" for root, "../" for /how/
    nav_html = "\n    ".join(
        f'<a href="{p}{href if not href.startswith("/") else href.lstrip("/")}"'
        + (' class="active" aria-current="page"' if lbl == ACTIVE_KEY[page_id] else "")
        + f">{lbl}</a>"
        for lbl, href in NAV)
    cta_href = CTA_NAV[1].lstrip("/")
    nav_html += f'\n    <a class="btn-nav" href="{p}{cta_href}">{CTA_NAV[0]}</a>'
    footer = FOOTER_COLS.replace("{URL}", p)
    ogimg = canonical.rstrip("/").rsplit("/", 1)[0] + "/og-image.png" if False else f"{p}og-image.png"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://manyaai.github.io/openshelter/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b6e66">
<link rel="canonical" href="{canonical}">
<link rel="sitemap" type="application/xml" href="{p}sitemap.xml">
<link rel="icon" type="image/svg+xml" href="{p}favicon.svg">
<link rel="apple-touch-icon" href="{p}assets/apple-touch-icon.png">
<link rel="preload" href="{p}css/inter.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{p}css/inter.css"></noscript>
<script>if(!CSS.supports||!CSS.supports('font-family','Inter')){{document.write('<link rel="stylesheet" href="{p}css/fonts.css">')}}</script>
<link rel="stylesheet" href="{p}css/style.css">
<link rel="stylesheet" href="{p}css/dark.css">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap">
  <a class="brand" href="{p}index.html"><img src="{p}logo.svg" alt="OpenShelter logo: shelter roof with compliance checkmark"><span><b class="wordmark">OpenShelter</b><small>safer shelters, open by default</small></span></a>
  <button class="nav-toggle" type="button" aria-label="Menu" aria-expanded="false"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button>
  <nav class="nav" aria-label="Main navigation">
    {nav_html}
    <span class="nav-tools"><button class="theme-toggle" type="button" aria-label="Toggle dark mode"><svg class="ic-moon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><svg class="ic-sun" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button></span>
  </nav>
</div></header>
{crumbs(page_id, p)}
<main id="main">
{body}
{pager(page_id, p)}
</main>
<footer class="site"><div class="wrap">
{footer}  <div class="fine">© <span class="year">2026</span> OpenShelter contributors · Not a substitute for a licensed structural engineer</div>
</div></footer>
<button class="totop" aria-label="Back to top">↑</button>
<script src="{p}js/ui.js"></script>
{scripts}
</body>
</html>"""

# ---------------------------------------------------------------- home sections
HERO = """
<section class="hero"><div class="wrap">
  <span class="eyebrow">Digital public infrastructure · AGPL-3.0</span>
  <h1>Every community deserves a shelter designed for <em>its</em> hazards.</h1>
  <p class="lead">OpenShelter turns public hazard data and published building codes into plain-language, printable design briefs, where <b>every recommendation cites the clause and the measurement behind it.</b> No black boxes. No fees. No vendor lock-in.</p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="demo/">Try the live demo →</a>
    <a class="btn btn-outline" href="briefs/">See example briefs</a>
  </div>
  <div class="hero-stats">
    <div class="hs"><b>5</b><span>building-code profiles shipped</span></div>
    <div class="hs"><b>2</b><span>real public hazard datasets wired in</span></div>
    <div class="hs"><b>100%</b><span>open source, diffable in git</span></div>
    <div class="hs"><b>$0</b><span>free for governments &amp; classrooms</span></div>
  </div>
  <div class="trust-row">
    <span class="pill"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.5-3 8.5-7 10-4-1.5-7-5.5-7-10V6z"/><path d="M9 12l2 2 4-4"/></svg>Runs in your browser, nothing uploaded</span>
    <span class="pill"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 12h7M9 16h7"/></svg>Every rule cites its code clause</span>
    <span class="pill"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 10h8M8 14h5"/></svg>Deterministic: same input, same brief, forever</span>
    <span class="pill"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12a7 7 0 0 1 14 0"/><path d="M8.5 15a3.5 3.5 0 0 1 7 0"/><circle cx="12" cy="18.5" r="1"/><path d="M3 3l18 18"/></svg>Works offline on a field laptop</span>
  </div>
  <div class="hero-map" id="hzmap" role="img" aria-label="World map of famous high-risk sites; click any marker to generate a brief"></div>
  <p class="map-note" id="maphint" style="display:none">Click a glowing marker, or anywhere on the map, to generate that site's design brief instantly.</p>
</div></section>
"""

DEMO = """
<section id="demo" class="reveal"><div class="wrap"><div class="card demo-card">
  <h2>Generate a design brief, in your browser, right now</h2>
  <p class="hint" id="datastatus">Loading hazard data…</p>
  <form class="demo" id="f">
    <div class="fld" style="grid-column:1/-1"><label for="preset">Pick a famous high-risk site (auto-generates)</label>
      <select id="preset">
        <option value="">- or enter coordinates manually below -</option>
        <option value="23.81,90.41">Dhaka, Bangladesh, flood / cyclone / heat</option>
        <option value="14.60,120.98">Manila, Philippines, typhoon / earthquake</option>
        <option value="41.01,28.98">Istanbul, Türkiye, earthquake</option>
        <option value="18.54,-72.26">Port-au-Prince, Haiti, earthquake / hurricane</option>
        <option value="21.43,92.01">Cox's Bazar, Bangladesh, cyclone / landslide</option>
        <option value="19.43,-99.13">Mexico City, Mexico, seismic</option>
        <option value="35.68,139.65">Tokyo, Japan, earthquake / typhoon</option>
        <option value="-19.83,34.86">Beira, Mozambique, cyclone / flood</option>
        <option value="-18.12,178.45">Suva, Fiji, cyclone / sea-level rise</option>
        <option value="-6.21,106.85">Jakarta, Indonesia, earthquake / flood</option>
      </select></div>
    <div class="fld"><label for="lat">Latitude</label><input id="lat" type="number" step="0.01" min="-90" max="90" value="23.81" required></div>
    <div class="fld"><label for="lon">Longitude</label><input id="lon" type="number" step="0.01" min="-180" max="180" value="90.39" required></div>
    <div class="fld"><label for="code">Building code profile</label><select id="code">
        <option value="in-is139-is4352">India, IS 139 / IS 4352</option>
        <option value="eu-eurocode-8">EU, Eurocode 8</option>
        <option value="us-iebc">USA, IBC / ASCE 7</option>
        <option value="ph-nscc">Philippines, NSCP</option>
        <option value="sphere-humanitarian">Sphere humanitarian standards</option>
      </select></div>
    <div class="fld"><label for="pop">People sheltered</label><input id="pop" type="number" min="0" value="5000"></div>
    <div class="fld"><label for="water">Distance to river/coast (m)</label><input id="water" type="number" min="0" value="5000"></div>
    <button class="go" type="submit">Generate design brief</button>
  </form>
  <div id="out" aria-live="polite"></div>
  <div class="disclaimer"><b>Honesty policy.</b> Earthquake &amp; cyclone scores come from real public-domain data (USGS ComCat M6.0+ 1990-2026; NOAA IBTrACS climatology). Flood, heat, drought and landslide values are labelled demo placeholders until national agencies contribute authoritative layers. OpenShelter produces pre-design guidance, not stamped engineering, a licensed local engineer must verify structural calculations before construction.</div>
</div></div></section>
"""

HOME_TEASERS = """
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">The problem in one paragraph</span><h2>Safe knowledge exists. It just isn't connected.</h2></div>
  <p style="color:var(--ink-soft);font-size:1.08rem">Billions of dollars flow into emergency shelters every year. Most are designed from copy-paste templates that ignore local codes and local hazards, so the same "safe" shelter that survives an earthquake in one country collapses in a flood somewhere else. Hazard maps exist. Building codes exist. Nothing free and auditable connected them, <b>until now.</b></p>
  <p><a class="btn btn-outline btn-sm" href="how/">Read the full explanation →</a></p>
</div></section>
"""

# ---------------------------------------------------------------- HOW page
HOW_BODY = """
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Method</span><h1>Three deterministic steps, no AI guessing</h1>
  <p class="lead">Governments spending public money must answer one question at audit time: <i>who decided this, and on what basis?</i> OpenShelter can answer it line by line. Here is exactly how a brief is produced.</p>
</div></section>
<div class="wrap"><div class="grid grid-3">
  <div class="card tile"><span class="num">1</span><h3>Hazard fingerprint</h3><p>Your coordinates are looked up in gridded public datasets, USGS earthquakes and NOAA cyclone tracks today; national flood &amp; heat layers next. Every value carries its source label, and the engine refuses to hide which is which.</p></div>
  <div class="card tile"><span class="num">2</span><h3>Code profile</h3><p>Each jurisdiction's rules (Eurocode 8, IS 139, ASCE 7, NSCP, Sphere) live in machine-readable JSON anyone can inspect, diff and correct via pull request, owned by the countries themselves, not by a vendor.</p></div>
  <div class="card tile"><span class="num">3</span><h3>Rule engine</h3><p>Hazard × code produces ranked measures and compliance checks. Same inputs → byte-identical brief, forever. That determinism is what makes the output usable in audits, procurement and court-grade documentation.</p></div>
</div></div>
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Walkthrough</span><h2>What happens when you click "Generate"</h2></div>
  <ol class="steps">
    <li><b>Inputs are normalised.</b> Latitude, longitude, population served and distance to water become a <code>Site</code> record. Nothing leaves your browser; the same code runs offline in the Python CLI.</li>
    <li><b>The hazard grid is sampled.</b> Real grids (earthquake, cyclone) are read from bundled JSON derived from public-domain catalogues. Placeholder layers are computed deterministically and <u>flagged as demo</u> in the output itself.</li>
    <li><b>The code profile is loaded.</b> A JSON file like <code>in-is139-is4352.json</code> contains thresholds, clauses and citations, e.g. <i>"set floor level ≥ 0.6 m above highest recorded flood; cite IS 139 §4.2"</i>.</li>
    <li><b>Rules fire in priority order.</b> Each triggered rule emits a recommendation carrying: priority (P1 critical → P3 advisable), the hazard value that fired it, and the exact clause reference.</li>
    <li><b>Compliance checks run.</b> Machine-verifiable pass/review states (occupancy area per person, WASH ratios, freeboard) are computed against your population figure.</li>
    <li><b>The brief renders.</b> JSON, Markdown or printable HTML, all three diff-stable, version-stamped, and citable by URL.</li>
  </ol>
</div></section>
<section class="tight reveal" style="background:#fff;border-block:1px solid var(--line)"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Principles</span><h2>Why "explainable" beats "smart"</h2></div>
  <details open><summary>A model that can't cite a clause can't survive an audit</summary><div class="d-body"><p>Neural networks are brilliant at pattern-matching and hopeless at accountability. When a ministry defends shelter spending before a public accounts committee, "the algorithm said so" is not an answer. Every OpenShelter recommendation prints the hazard value and the exact code clause that produced it. No hidden model, no proprietary data, no subscription.</p></div></details>
  <details><summary>What it deliberately does NOT do</summary><div class="d-body"><p>It does not replace a licensed structural engineer, stamp drawings, or claim site-specific geotechnical truth. It closes the gap between "no plan at all" and "an unaffordable consultancy" by producing the pre-design brief that makes the engineer's job faster, cheaper and locally appropriate.</p></div></details>
  <details><summary>Determinism is a feature, not a limitation</summary><div class="d-body"><p>There is no randomness, no learning-at-runtime, no telemetry-dependent behaviour. Given identical inputs and an identical code-profile version, OpenShelter will produce the same brief in 2030 that it produces today, which is precisely what archivists, auditors and litigators need.</p></div></details>
  <details><summary>Federated ownership of legal text</summary><div class="d-body"><p>Building-code wording is copyrighted in many jurisdictions, and getting it wrong has legal consequences. So each national profile is a declarative JSON file maintained through pull requests reviewed by (ideally) that country's standards community. Adding Bangladesh's BNBC does not require waiting on the core team, it requires one file and one PR.</p></div></details>
</div></section>
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Under the hood</span><h2>The stack, honestly listed</h2></div>
  <div class="card" style="padding:var(--s3)"><table class="src">
    <tr><th>Component</th><th>Technology</th><th>Why it matters</th></tr>
    <tr><td>Engine (CLI)</td><td>Python ≥3.9, stdlib only</td><td>Runs on a field laptop with no internet and no pip installs</td></tr>
    <tr><td>Engine (browser)</td><td>Vanilla JS port, zero dependencies</td><td>The demo is the same logic, not a marketing mock-up</td></tr>
    <tr><td>Code profiles</td><td>Versioned JSON + CI validator</td><td>Diffable, citable, reviewable like Wikipedia</td></tr>
    <tr><td>Hazard data</td><td>Public-domain grids (USGS, NOAA); raster interface ready</td><td>No licence fees, no vendor lock-in, ever</td></tr>
    <tr><td>This website</td><td>Static HTML generated by <code>tools/build_site.py</code></td><td>No framework, no build service to break, hosts anywhere</td></tr>
  </table></div>
  <p style="margin-top:var(--s3)"><a class="btn btn-primary" href="../demo/">Try it now →</a>&nbsp;&nbsp;<a class="btn btn-outline btn-sm" href="../trust/">See data provenance</a></p>
</div></section>
"""

# ---------------------------------------------------------------- TRUST page
TRUST_BODY = """
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Transparency</span><h1>Data sources &amp; honesty policy</h1>
  <p class="lead">Trust is not claimed here; it is evidenced. Every layer below is either public-domain data with a citation, a published standard with a clause number, or explicitly labelled a demo placeholder. This transparency <i>is</i> the product.</p>
</div></section>
<section class="tight"><div class="wrap measure-wide">
  <div class="card" style="padding:var(--s3)">
  <table class="src">
    <tr><th>Layer</th><th>Source used today</th><th>Status</th></tr>
    <tr><td><b>Earthquake</b></td><td><a href="https://earthquake.usgs.gov/data/comcat/">USGS ComCat</a> catalogue, M6.0+ events 1990-2026 (public domain), decay-kernel interpolated to a 0.5° grid shipped with the site</td><td><span class="badge pass">REAL DATA</span></td></tr>
    <tr><td><b>Cyclone</b></td><td><a href="https://www.ncei.noaa.gov/products/international-best-track-analysis-system">NOAA IBTrACS</a> tropical-cyclone best-track climatology (public domain), storm-track density by basin</td><td><span class="badge pass">REAL DATA</span></td></tr>
    <tr><td><b>Flood / Heat / Drought / Landslide</b></td><td>Deterministic synthetic field for demonstration; swap-in interface ready for GEM Risk Library &amp; Copernicus EMS rasters</td><td><span class="badge review">DEMO, clearly labelled</span></td></tr>
    <tr><td><b>Building codes</b></td><td>5 curated profiles citing published standards: Eurocode 8 &amp; EPBD recast, IBC/ASCE 7/FEMA P-361, IS 139/IS 4352 &amp; NSCP 2010, Sphere Handbook</td><td><span class="badge pass">CITED CLAUSES</span></td></tr>
  </table></div>
</div></section>
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Accountability</span><h2>Our honesty commitments</h2></div>
  <ul class="checks">
    <li>We label demo values as demo values, inside the generated brief itself, not just in a footnote.</li>
    <li>We publish the full derivation: dataset, version, date fetched, interpolation method.</li>
    <li>We never present output as stamped engineering; every brief names the licensed-engineer step.</li>
    <li>We accept corrections like Wikipedia: fix a clause, merge a PR, everyone benefits.</li>
    <li>The browser demo uploads nothing. The CLI needs no internet once installed.</li>
  </ul>
</div></section>
<section class="tight reveal" style="background:#fff;border-block:1px solid var(--line)"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">FAQ</span><h2>Questions reviewers actually ask</h2></div>
  <details><summary>Is this a replacement for engineers or consultants?</summary><div class="d-body"><p>No, and we refuse to pretend otherwise. OpenShelter produces the pre-design brief: hazard-appropriate systems, code-cited constraints, and compliance checks. A licensed local engineer performs the structural calculations and signs the drawings. Our aim is to make that engagement cheaper and better-informed, not optional.</p></div></details>
  <details><summary>Why are some hazard values still "demo"?</summary><div class="d-body"><p>Flood and heat authority comes from national agencies, not from us inventing numbers. Rather than ship unlabeled guesses, we show clearly-marked placeholders and provide the plug-in interface (and funding roadmap) for agencies to contribute their own raster layers via pull request.</p></div></details>
  <details><summary>Who governs the code profiles? Could someone sabotage them?</summary><div class="d-body"><p>Profiles are JSON files with citations, reviewed in pull requests, validated by CI, and intended to be co-owned by each country's standards community. Governance structure is documented in docs/GOVERNANCE.md; changes are traceable by git history like Wikipedia revisions.</p></div></details>
  <details><summary>How is this funded? What's the catch?</summary><div class="d-body"><p>AGPL-3.0 means the tool is free forever; sustainability comes from paid localization contracts (a ministry commissions its own code profile and hosted instance), foundation grants (Sendai-aligned DRR funding), and dual licensing for commercial integrators. There is no user paywall and no data monetisation, see docs/FUNDING.md.</p></div></details>
  <details><summary>Can a government rely on this in procurement?</summary><div class="d-body"><p>The briefs are designed to be attached to tender documents as <i>requirements definitions</i>, deterministic, version-stamped and citable. Procurement law differs by country; consult your legal team, but the audit trail (rule → hazard value → clause) is exactly what evaluation committees ask for.</p></div></details>
  <details><summary>Does it work without internet?</summary><div class="d-body"><p>Yes. The Python CLI is stdlib-only and ships its grids as JSON; the browser demo caches everything on first load. Field teams routinely operate on prepaid connections, offline-first is a requirement, not a nicety.</p></div></details>
</div></section>
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Alignment</span><h2>Frameworks this project supports</h2></div>
  <div class="grid grid-3">
    <div class="card tile"><h3>Sendai Framework</h3><p>Target E: increase national DRR strategies. OpenShelter turns a country's own hazard data and codes into implementable shelter requirements.</p></div>
    <div class="card tile"><h3>EU open-source doctrine</h3><p>Federal Source Code Policy-style reuse, "public code" procurement preferences, Horizon Europe digital-public-infrastructure calls.</p></div>
    <div class="card tile"><h3>Sphere &amp; CHS</h3><p>Humanitarian standards encoded directly: shelter space per person, WASH ratios, and accessibility checks ship in the default profile.</p></div>
  </div>
  <p style="margin-top:var(--s3)"><a class="btn btn-outline btn-sm" href="https://github.com/Manyaai/openshelter/blob/main/docs/STANDARDS.md">Full standards mapping →</a></p>
</div></section>
"""

# ---------------------------------------------------------------- CONTRIBUTE page
CONTRIBUTE_BODY = """
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Get involved</span><h1>Ten minutes, three ways, pick your difficulty</h1>
  <p class="lead">OpenShelter's fragile part (legal code text) is designed to be owned by many hands. You don't need to write Python to make a shelter safer.</p>
</div></section>
<section class="tight"><div class="wrap">
  <div class="grid grid-3">
    <div class="card tile"><span class="lvl easy">EASY</span><h3>Fix a number like Wikipedia</h3><p>Every rule lives in plain JSON with citations. Spot a wrong threshold or missing clause? Edit the file, open a pull request, CI validates it. Non-coders can open an issue describing the fix and we'll pair with you.</p><a class="btn btn-outline btn-sm" href="https://github.com/Manyaai/openshelter/issues/new/choose">Report a correction →</a></div>
    <div class="card tile"><span class="lvl mid">MEDIUM</span><h3>Add your country's code</h3><p>One command scaffolds a validated profile:<br><code>python tools/new_code_profile.py --id bd-bnbc --jurisdiction BD --name "Bangladesh National Building Code"</code><br>Fill the JSON with clause references, run the validator, submit. We review within days and credit you (or your agency) in the profile metadata.</p><a class="btn btn-outline btn-sm" href="https://github.com/Manyaai/openshelter/blob/main/CONTRIBUTING.md">Contributing guide →</a></div>
    <div class="card tile"><span class="lvl hard">ANY SIZE</span><h3>Translate &amp; teach</h3><p>Bengali, Spanish and French first, help a non-English-speaking municipality use the tool. Or adopt the CLI in a risk-engineering studio: students shipping a real upstream code profile beats another toy assignment.</p><a class="btn btn-outline btn-sm" href="https://github.com/Manyaai/openshelter/discussions">Start a discussion →</a></div>
  </div>
</div></section>
<section class="tight reveal" style="background:#fff;border-block:1px solid var(--line)"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">For institutions</span><h2>Agencies, ministries &amp; NGOs</h2></div>
  <ul class="checks">
    <li><b>Own your numbers.</b> Publish your national flood/heat grids as a provider plugin, your scientists review the PR, your ministry gets named provenance in every brief.</li>
    <li><b>Commission a profile.</b> Fund the encoding of your building code (typically weeks of work, not months) and it stays open for every citizen forever.</li>
    <li><b>Pilot a deployment.</b> We're looking for 2-3 pilot municipalities to run real reconstruction briefs end-to-end and publish the results.</li>
  </ul>
  <p><a class="btn btn-primary" href="https://github.com/Manyaai/openshelter/blob/main/docs/FUNDING.md">Funding &amp; partnership pathways →</a></p>
</div></section>
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Good first issues</span><h2>Where contributors usually start</h2></div>
  <ol class="steps">
    <li><b>Harden the raster interface</b>, wire the GEM Risk Library / Copernicus DEM providers into <code>core/hazard.py</code> (interface already exists).</li>
    <li><b>Profile clinics</b>, pair with a standards engineer to encode BNBC (Bangladesh), NBC (Nepal), or Caribbean Uniform Building Code.</li>
    <li><b>PDF export</b>, one clean print-ready template for briefs, requested by every pilot conversation so far.</li>
    <li><b>i18n strings</b>, extract UI copy into JSON locales; Bengali translation is drafted and waiting.</li>
  </ol>
  <p style="color:var(--muted);font-size:.9rem">Code of conduct: be kind, cite sources, assume good faith. AGPL keeps every contribution open, that's the deal, and it's why people contribute.</p>
</div></section>
"""

# ---------------------------------------------------------------- MISSION (kept from existing file, wrapped)
MISSION_BODY = """
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Our reason for existing</span><h1>Mission, vision &amp; the story so far</h1>
  <p class="lead">A world where \"we couldn't afford a safe design\" is no longer a reason a shelter fails.</p>
</div></section>
<div class="wrap"><main class="doc" style="padding-left:0;padding-right:0">
  <div class="mv">
    <div><h3>Our mission</h3>Give every community, regardless of budget, the ability to design emergency shelters that respect their country's hazards and its own building codes, with every decision traceable to a public source.</div>
    <div><h3>Our vision</h3>A world where \"we couldn't afford a safe design\" is no longer a reason a shelter fails. Public safety knowledge stays public: open data in, auditable guidance out, forever free for governments, NGOs and classrooms.</div>
    <div><h3>Why now</h3>Climate displacement is rising, shelter budgets are under pressure, and digital public infrastructure is finally its own funding category (EU, UN, national DRR strategies). The gap between hazard science and a buildable checklist is exactly what an open project can close.</div>
  </div>

  <blockquote>The best time to fix a shelter design is before the monsoon, not after the funeral.</blockquote>

  <h2>The problem we refuse to accept</h2>
  <p>After every disaster, the same story repeats: temporary shelters built from generic templates, reused for years, failing in the next event because they were designed for the last one's hazard, or none at all. Satellite dashboards tell officials <i>where</i> floods happen. Thick code PDFs tell engineers <i>how</i> to build against them. Between those two documents sits a village waiting for a shelter that accounts for both.</p>
  <p>No one owns that gap. Commercial risk software is proprietary and priced for insurers; government consultants produce one-off reports; open data sits unused. We built the bridge: a tool small enough to run offline on a field laptop, transparent enough to survive a procurement audit, and open enough that a standards body in Dhaka or Manila can own its own numbers without asking a vendor for permission.</p>

  <h2>The story so far</h2>
  <div class="card" style="padding:var(--s3)">
  <ul class="road">
    <li><b>v0.1 · The foundation.</b> Five machine-readable code profiles (Eurocode 8, IBC/ASCE 7, IS 139, NSCP, Sphere), a deterministic rule engine where every output cites its clause, a CLI that runs on stdlib-only Python, and full test coverage.</li>
    <li><b>v0.2 · Real data + a public front door.</b> USGS earthquake and NOAA cyclone climatology wired into both the Python core and a browser demo. A live multi-page website, brief gallery, governance docs and a funding map published.</li>
    <li><b>Next · Country ownership.</b> Flood and heat layers contributed by national agencies through pull requests they control, the first ones are why we're talking to disaster-management ministries today.</li>
  </ul>
  </div>

  <h2>What we will never do</h2>
  <ol style="color:var(--ink-soft);padding-left:1.3rem">
    <li>Sell or gatekeep safety knowledge behind a paywall.</li>
    <li>Hide a recommendation behind a model that cannot cite a clause.</li>
    <li>Pretend to replace a licensed structural engineer, we make their work faster and cheaper, not optional.</li>
    <li>Ship a number without labelling where it came from, even when \"demo placeholder\" is an embarrassing answer.</li>
  </ol>

  <h2>Values</h2>
  <ul style="color:var(--ink-soft);padding-left:1.3rem">
    <li><b>Auditable beats clever.</b> Every output cites its inputs. No black boxes, ever.</li>
    <li><b>Honest about limits.</b> Demo data is labelled demo data; we say plainly when a licensed engineer is required.</li>
    <li><b>Local ownership.</b> Countries maintain their own code profiles through pull requests they control.</li>
    <li><b>Boring technology.</b> Plain text, JSON, git, deterministic rules, tools archivists and auditors love.</li>
  </ul>

  <h2>The road ahead</h2>
  <div class="card" style="padding:var(--s3)">
  <ul class="road">
    <li><b>Now:</b> real raster-backed flood &amp; heat providers (GEM Risk Library, Copernicus), first pilot municipality, more code profiles.</li>
    <li><b>Next:</b> i18n (Bengali, Spanish, French), PDF export, a public registry of adopted briefs.</li>
    <li><b>Later:</b> an independent foundation holding the trademark and roadmap, funded the way Wikipedia and OSI fund open infrastructure.</li>
  </ul>
  </div>

  <p style="margin-top:var(--s4)"><a class="btn btn-primary" href="../demo/">Try the live demo →</a>&nbsp;&nbsp;<a class="btn btn-outline" href="https://github.com/Manyaai/openshelter/blob/main/docs/FUNDING.md">Partner with us / funding pathways</a></p>
</main></div>
"""

# ---------------------------------------------------------------- BRIEFS gallery
def briefs_body() -> str:
    entries = []
    meta = {
        "dhaka-bangladesh.html": ("Dhaka, Bangladesh", "heatwave-dominant", "IS 139 / IS 4352 profile"),
        "manila-philippines.html": ("Manila, Philippines", "flood-dominant", "NSCP 2010 profile"),
        "istanbul-trkiye.html": ("Istanbul, Türkiye", "seismic/flood context", "Eurocode 8 profile"),
        "port-au-prince-haiti.html": ("Port-au-Prince, Haiti", "heatwave-dominant", "IBC / ASCE 7 profile"),
        "coxs-bazar-camp-bangladesh.html": ("Cox's Bazar Camp, Bangladesh", "heatwave-dominant", "Sphere humanitarian profile"),
    }
    cards = []
    for fname, (name, dom, prof) in meta.items():
        cards.append(f'''    <div class="card tile"><h3>{name}</h3><p><span class="badge p1">{dom}</span><br>{prof}<br><a href="{fname}">Open printable brief &rsaquo;</a></p></div>''')
    cards.append('''    <div class="card tile" style="border-style:dashed"><h3>Want your city here?</h3><p>Run the <a href="../demo/">live demo</a> or contribute your country's code profile. Gallery entries are generated by CI from the same engine.<br><a href="https://github.com/Manyaai/openshelter/blob/main/CONTRIBUTING.md">Contributing guide &rsaquo;</a></p></div>''')
    return f"""
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Proof, not promises</span><h1>Sample design briefs</h1>
  <p class="lead">Every file below is a real end-to-end output of the OpenShelter engine, generated by the same Python code that powers the CLI, opened exactly as a field team would print it. Hazard values carry source labels; recommendations carry code citations.</p>
</div></section>
<section class="tight"><div class="wrap"><div class="grid grid-2">
{chr(10).join(cards)}
</div>
<p class="hint" style="margin-top:var(--s3)">Note: these gallery briefs were generated with v0.1's labelled synthetic hazard field; the <a href="../demo/">live demo</a> uses real USGS/NOAA grids for earthquake &amp; cyclone scores.</p>
</div></section>
"""

# ---------------------------------------------------------------- DEMO page (standalone)
DEMO_SCRIPTS = '<script src="briefgen.js"></script>\n<script src="js/demo.js"></script>'

def demo_body() -> str:
    return f"""
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Try it now</span><h1>Generate a shelter design brief, right in your browser</h1>
  <p class="lead">Pick a famous high-risk site or type any coordinates. The tool reads real earthquake and cyclone data, applies the building code you choose, and prints a plain-language brief where every recommendation cites its source. Nothing is uploaded; this runs entirely on your device.</p>
</div></section>
<div class="wrap">{{DEMO_CARD}}</div>
""".replace("{DEMO_CARD}", DEMO.replace('<section id="demo" class="reveal">', '<section class="tight">').replace("</section>", "</section>", 1))

# ---------------------------------------------------------------- NEWSROOM
NEWS_POSTS = [
    dict(date="2026-10-19", tag="Release", title="Site rebuilt as a multi-page experience",
         body="The single long scroll became eight focused pages with breadcrumbs, prev/next navigation and a standalone live-demo page. Same engine, clearer journey."),
    dict(date="2026-10-12", tag="Data", title="Real hazard data wired in: USGS and NOAA",
         body="Earthquake scores now derive from the USGS ComCat catalogue (M6.0+, 1990-2026) and cyclone scores from NOAA IBTrACS climatology, both public domain. Every other layer stays clearly labelled as a demo placeholder until national agencies contribute authoritative grids."),
    dict(date="2026-10-05", tag="Community", title="Code profiles are now community-owned",
         body="Adding a country means one JSON file and one pull request, scaffolded by a single command. Eurocode 8, IBC/ASCE 7, IS 139, NSCP and Sphere ship today; Bangladesh's BNBC is in review."),
    dict(date="2026-09-28", tag="Release", title="v0.2: deterministic briefs, three formats",
         body="JSON for machines, Markdown for repositories, printable HTML for field teams. Byte-identical output for identical inputs, so a brief produced today can be cited verbatim in an audit next decade."),
]

def news_body(p: str) -> str:
    posts = []
    for n in NEWS_POSTS:
        posts.append(f'''<article class="card tile post"><div class="post-meta"><time>{n["date"]}</time><span class="badge info">{n["tag"]}</span></div><h3>{n["title"]}</h3><p>{n["body"]}</p></article>''')
    return f"""
<section class="page-head"><div class="wrap measure-narrow">
  <span class="kicker">Newsroom</span><h1>What changed, and when</h1>
  <p class="lead">A running log of releases, data upgrades and community milestones. Plain dates, no marketing gloss, because auditors and grant reviewers read changelogs.</p>
</div></section>
<section class="tight"><div class="wrap measure-wide grid grid-1">
{chr(10).join(posts)}
</div></section>
<section class="tight reveal"><div class="wrap measure">
  <div class="sec-head"><span class="kicker">Roadmap</span><h2>What's coming next</h2></div>
  <ul class="checks">
    <li><b>National flood &amp; heat layers</b>, contributed through pull requests by the agencies that own those numbers.</li>
    <li><b>PDF export</b> for briefs, the most-requested feature from pilot conversations.</li>
    <li><b>Bengali, Spanish and French interfaces</b> so municipalities can use the tool in their own language.</li>
    <li><b>First pilot municipality</b>, publishing a real reconstruction brief end-to-end.</li>
  </ul>
  <p><a class="btn btn-outline btn-sm" href="{p}contribute/">Help build it &rarr;</a></p>
</div></section>
"""

# ---------------------------------------------------------------- write pages
def w(relpath: str, content: str):
    dest = SITE / relpath
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    print("wrote", relpath, len(content), "bytes")

BASE = "https://manyaai.github.io/openshelter"


def build_404():
    """Self-contained branded 404 page for GitHub Pages."""
    css = (SITE / "css" / "style.css").read_text(encoding="utf-8")
    dark = (SITE / "css" / "dark.css").read_text(encoding="utf-8")
    logo = (SITE / "logo.svg").read_text(encoding="utf-8") if (SITE / "logo.svg").exists() else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found | OpenShelter</title>
<style>
{css}
{dark}
.nf-wrap{{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}}
.nf-card{{max-width:640px;text-align:center;background:var(--card,#fff);border:1px solid var(--line,#e4e1d8);border-radius:16px;padding:3rem 2rem}}
.nf-logo svg{{height:56px;width:auto;margin:0 auto .5rem}}
.nf-code{{font-size:4rem;font-weight:800;color:var(--brand,#0b6e66);margin:0;line-height:1}}
.nf-links{{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;margin-top:1.5rem}}
.nf-note{{margin-top:1.5rem;font-size:.9rem;color:var(--muted,#61798a)}}
</style>
<link rel="icon" href="/openshelter/favicon.svg" type="image/svg+xml">
</head>
<body>
<main id="main" class="nf-wrap">
  <div class="nf-card">
    <div class="nf-logo">{logo}</div>
    <p class="nf-code">404</p>
    <h1>This page moved or never existed</h1>
    <p>No shelter was harmed. The link you followed points somewhere we don't have yet.</p>
    <nav class="nf-links" aria-label="Site pages">
      <a class="btn btn-primary" href="/openshelter/">Home</a>
      <a class="btn" href="/openshelter/how/">How it works</a>
      <a class="btn" href="/openshelter/demo/">Live demo</a>
      <a class="btn" href="/openshelter/briefs/">Example plans</a>
      <a class="btn" href="/openshelter/trust/">Trust &amp; data</a>
      <a class="btn" href="/openshelter/news/">Newsroom</a>
      <a class="btn" href="/openshelter/contribute/">Get involved</a>
    </nav>
    <p class="nf-note">Something broken? <a href="https://github.com/Manyaai/openshelter/issues/new">Tell us on GitHub</a>.</p>
  </div>
</main>
</body>
</html>"""
    w("404.html", page)


def main():
    # HOME
    home = layout("home",
        "OpenShelter, open-source multi-hazard shelter design advisor",
        "Free, auditable tool turning public hazard data + real building codes into plain-language shelter design briefs. Try the live demo, runs in your browser, nothing uploaded.",
        "", HERO + DEMO + HOME_TEASERS, BASE + "/",
        extra_head='<link rel="stylesheet" href="css/vendor/leaflet/leaflet.css">\n<script type="application/ld+json">{"@context":"https://schema.org","@type":"SoftwareApplication","name":"OpenShelter","applicationCategory":"UtilitiesApplication","operatingSystem":"Any","offers":{"@type":"Offer","price":"0","priceCurrency":"USD"},"description":"Open-source multi-hazard resilient shelter design advisor producing auditable, code-cited shelter design briefs.","codeRepository":"https://github.com/Manyaai/openshelter","license":"https://spdx.org/licenses/AGPL-3.0-or-later.html"}</script>',
        scripts='<script src="js/leaflet.js"></script>\n<script src="briefgen.js"></script>\n<script src="js/demo.js"></script>')
    w("index.html", home)

    # HOW
    w("how/index.html", layout("how",
        "How it works, OpenShelter",
        "Three deterministic steps: hazard fingerprint, machine-readable code profile, explainable rule engine. Why 'explainable' beats 'smart' for public safety.",
        "../", HOW_BODY, BASE + "/how/"))

    # TRUST
    w("trust/index.html", layout("trust",
        "Data sources & honesty policy, OpenShelter",
        "Real USGS/NOAA data where available, clearly-labelled demo placeholders elsewhere, cited code clauses everywhere. FAQ on engineering liability, governance and funding.",
        "../", TRUST_BODY, BASE + "/trust/"))

    # CONTRIBUTE
    w("contribute/index.html", layout("contribute",
        "Contribute, OpenShelter",
        "Add your country's building code as one JSON file, correct a number like Wikipedia, translate the interface, or pilot a municipal deployment.",
        "../", CONTRIBUTE_BODY, BASE + "/contribute/"))

    # BRIEFS
    w("briefs/index.html", layout("briefs",
        "Brief gallery, OpenShelter",
        "Real end-to-end shelter design briefs generated by the OpenShelter engine for five high-risk locations.",
        "../", briefs_body(), BASE + "/briefs/"))

    # DEMO (standalone page, same engine as the home widget)
    w("demo/index.html", layout("demo",
        "Live demo, generate a shelter design brief",
        "Enter coordinates or pick a high-risk city, choose a building code, and get a plain-language, code-cited shelter design brief. Runs in your browser; nothing uploaded.",
        "../", demo_body(), BASE + "/demo/",
        scripts='<script src="../briefgen.js"></script>\n<script src="../js/demo.js"></script>'))

    # NEWSROOM
    w("news/index.html", layout("news",
        "Newsroom & changelog, OpenShelter",
        "Release notes, data upgrades and community milestones, plus the public roadmap for OpenShelter.",
        "../", news_body("../"), BASE + "/news/"))

    # MISSION (reuse existing content, new chrome)
    w("mission/index.html", layout("mission",
        "Mission, Vision & Story, OpenShelter",
        "Why OpenShelter exists: our mission, vision, story, values and the road ahead.",
        "../", MISSION_BODY, BASE + "/mission/"))

    # SITEMAP
    urls = ["", "how/", "demo/", "briefs/", "trust/", "news/", "mission/", "contribute/"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sm.append(f" <url><loc>{BASE}/{u}</loc></url>")
    for b in ["dhaka-bangladesh", "manila-philippines", "istanbul-trkiye",
              "port-au-prince-haiti", "coxs-bazar-camp-bangladesh"]:
        sm.append(f" <url><loc>{BASE}/briefs/{b}.html</loc></url>")
    sm.append("</urlset>")
    w("sitemap.xml", "\n".join(sm))

    build_404()

if __name__ == "__main__":
    main()
