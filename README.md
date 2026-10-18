# OpenShelter

**Open-source, auditable multi-hazard resilient shelter design advisor.**

Give it a coordinate and a jurisdiction → get back a deterministic, plain-English
design brief for an emergency/transitional shelter aligned with *real* published
standards (Eurocode 8, IBC/ASCE 7/FEMA P-361, IS 13932, NSCP, Sphere Handbook…) —
with every recommendation citing the hazard data value and code clause that
produced it.

```bash
openshelter brief --lat 23.81 --lon 90.39 --code in-is139-is4352 --outdir out
```

## Why this exists

Every year, billions of public dollars (FEMA, ECHO, USAID/BHA, Green Climate
Fund, national disaster-management budgets) are spent on emergency and
transitional shelters. The design step today is either a **proprietary black
box**, **copy-paste templates** that ignore local hazards and codes, or nothing
at all — shelters get built ad hoc and fail in the next event.

OpenShelter closes the gap between *hazard science* and *a buildable, code-aware
brief* as free, reproducible software any municipality or ministry can run on a
laptop with zero licence fees.

## The unique bit

Most "disaster tech" answers *where* the hazard is (GIS). Almost nobody has
productised the machine-readable link between **open hazard data ↔ codified
building requirements ↔ a specific shelter design** in a form a small
municipality can actually use. That missing translation layer is exactly what
public agencies are mandated to provide — and fund:

| Layer | What ships here | Data provenance |
|---|---|---|
| Hazard fingerprint per site | `core/hazard.py` (pluggable providers) | GEM Risk Library, Copernicus EMS/ERA5, FAO SoilGrids (open licences) |
| Building-code registry | `data/codes/*.json`, maintained by authorities themselves | Eurocode 8/1991, EPBD recast, IBC 2024, ASCE 7-22, FEMA P-361, IS 13932/1893, NSCP 2015, Sphere 2018 |
| Explainable design engine | `core/engine.py` — every rule cites its inputs | WHO / IASC / Sphere shelter guidance |
| Audit-ready outputs | JSON + Markdown + printable HTML (`report/`) | schema-versioned, diff-able in git |

## Why it is sustainable & fundable

1. **Public-mandate alignment** — Sendai Framework Target E, climate-adaptation
   finance (GCF readiness), EU renovation/housing programmes and national DMO
   open-source mandates all fund exactly this tooling.
2. **Federated content model** — the risky-to-maintain part (legal code text)
   lives in declarative JSON profiles owned and PR'd by each national standards
   body; the software stays generic. Maintainers never become the bottleneck.
3. **Zero-dependency core** — stdlib-only Python runs offline on field laptops
   and Raspberry-Pi-class hardware; no SaaS lock-in, trivial hosting cost.
4. **Dual-licensing path** — AGPL for everyone; commercial licences for vendors
   embedding it in proprietary products (classic sustainable-OSS revenue).
5. **Contribution flywheel** — adding a country = adding one JSON file
   (`tools/new_code_profile.py` scaffolds and validates it). See CONTRIBUTING.md.

## Status

Early prototype (v0.1). The hazard layer currently uses a clearly-marked
**synthetic demo provider** so the whole pipeline runs offline and
deterministically in CI; wire real raster-backed providers before operational
use. Nothing here replaces a licensed structural engineer — it produces
pre-design briefs and compliance checklists.

## Quick start

```bash
git clone <this repo> && cd <repo>
python -m openshelter.cli.main codes          # list code profiles
python -m openshelter.cli.main brief \
       --lat 10.50 --lon 123.90 --code ph-nscc --outdir out
python -m openshelter.cli.main batch examples/sites.csv \
       --code sphere-humanitarian --outdir out/batch
python -m pytest tests/                        # 13 tests, stdlib only
```

## Layout

```
openshelter/
  core/     hazard.py · codes.py · engine.py      <- zero-dependency brain
  data/codes/*.json                               <- jurisdiction profiles (PR-able)
  report/   generators.py (JSON/MD/HTML)
  cli/      main.py
tools/      new_code_profile.py (profile scaffolder/validator)
docs/       STANDARDS.md · FUNDING.md · GOVERNANCE.md
tests/      deterministic unit tests
examples/   sites.csv
```

## Disclaimer

Deterministic pre-design aid. Structural sizing, anchorage and habitability
approvals remain the responsibility of locally licensed professionals.

## License

AGPL-3.0-only — see LICENSE. Commercial embedding licences available.
