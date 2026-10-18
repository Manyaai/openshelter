# OpenShelter website source

Static site published to https://manyaai.github.io/openshelter/ via `.github/workflows/pages.yml`.

- `index.html` — homepage + live browser demo (engine port in `briefgen.js`)
- `mission/`, `briefs/` — story page and sample-brief gallery
- `css/style.css` — design tokens ("Trusted civic" system); `css/dark.css` — dark mode
- `css/fonts/` — self-hosted Inter & Newsreader (OFL-1.1, no third-party requests)
- `js/leaflet.js` — Leaflet 1.9.4 (BSD-2) vendored for the interactive hazard map
- `data/` — code profiles JSON + gridded hazard data (USGS ComCat, NOAA IBTrACS)

Regenerate brand PNGs after editing SVGs: `python tools/gen_og_image.py` (needs `pip install cairosvg`).
All pages work without JavaScript except the map tiles; all JS works offline except basemap tiles.
