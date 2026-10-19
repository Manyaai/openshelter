# Changelog

All notable changes to OpenShelter are documented here. The website changelog
page (https://manyaai.github.io/openshelter/news/) mirrors this file.
Format follows Keep a Changelog; versions follow Semantic Versioning.

## [0.2.1] - 2026-10-19

### Added
- Multi-page static site: Home, How it works, Live demo, Example plans,
  Trust & data, Mission, Changelog, Get involved; branded 404 page.
- Interactive Leaflet hazard map with click-to-generate briefs (vendored,
  no CDN dependency).
- Browser demo ported from the Python engine (briefgen.js) with per-result
  data provenance panel and hazard fingerprint bars distinguishing real
  (USGS/NOAA) from demo layers.
- Dark mode with OS-preference + manual toggle; theme-regression guard in CI
  (tools/check_themes.py); link checker (tools/check_links.py) in CI.
- Real hazard integration v1: USGS ComCat earthquake scores, NOAA IBTrACS
  cyclone climatology; remaining layers clearly labelled as demo placeholders.
- Code-cited briefs for Eurocode 8, IBC/ASCE 7/FEMA P-361, IS 139 (India),
  NSCP (Philippines), Sphere standards; scaffold tool for new country
  profiles (tools/new_code_profile.py).

### Changed
- Header reduced to visitor-first navigation; secondary links moved to a
  structured three-column footer.
- Copy rewritten in plain language for non-technical readers; em dashes and
  emoji removed throughout.

### Fixed
- Footer/header/inputs invisible-on-white in dark mode (text token misused
  as background surface).
- Print stylesheet previously hid generated brief content; now hides only
  site chrome.

## [0.1.0] - 2026-09-28

### Added
- Deterministic rule engine producing JSON, Markdown, and printable HTML
  design briefs; every recommendation cites its hazard value and code clause.
- CLI (`openshelter codes|brief|batch`), five code profiles, synthetic offline
  hazard provider for reproducible demos, 13 passing tests.
