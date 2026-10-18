<p align="center">
  <img src="assets/logo-header.png" alt="OpenShelter — Free tools for safer emergency shelters" width="450"/>
</p>

# OpenShelter

**A free computer tool that helps communities design safer emergency shelters.**

When disasters strike, shelters get built in a hurry — often with templates that
ignore local floods, earthquakes, or heat. OpenShelter fixes that: you tell it
*where* the shelter will go, and it produces a plain-English **design brief**
based on real published building codes — and it explains *why* it recommends
each measure, citing the exact hazard data and code clause behind it.

## See it in action

```bash
pip install openshelter        # (until published, see "Try it now" below)
openshelter brief --lat 23.81 --lon 90.39 --code in-is139-is4352 --outdir out
```

You get three files: a JSON report, a readable Markdown brief, and a printable
HTML one-pager. Every recommendation looks like:

> **Raise the floor / build on higher ground.**
> Reason: modelled flood depth at this site is 0.8 m →
> Source: IS 13932 §4.2 (site selection), FEMA P-361.

## Try it now (no install needed yet)

```bash
git clone https://github.com/Manyaai/openshelter.git
cd openshelter
python -m openshelter.cli.main brief --lat 23.81 --lon 90.39 --code in-is139-is4352 --outdir out
python -m pytest        # 13 tests, all pass
```

## Who is this for?

- 🏛️ **Local governments & disaster agencies** — run it on an ordinary laptop, offline, licence-free
- 🔧 **NGOs & engineers** — start every shelter project from a code-aware, auditable brief
- 🎓 **Students & researchers** — a transparent reference implementation of hazard→code→design

## Why governments support projects like this

OpenShelter aligns with the **Sendai Framework** and open-source mandates many
countries already have (public code funded with public money stays public).
It turns billions of dollars of shelter spending from guesswork into
reproducible, auditable decisions. Details in [`docs/FUNDING.md`](docs/FUNDING.md).

## What's inside

| Folder | Purpose |
|---|---|
| `openshelter/core/` | Hazard lookup, building-code registry, the explainable design engine |
| `openshelter/data/codes/` | Machine-readable code profiles (Eurocode 8, IBC/ASCE 7/FEMA, IS 13932, NSCP, Sphere) |
| `openshelter/report/` | JSON / Markdown / printable HTML outputs |
| `docs/` | Standards mapping, funding roadmap, governance |
| `tests/` | Deterministic tests so results never change silently |

## Honest limitations

v0.1 uses clearly-marked **demo hazard data** to stay fully offline and
deterministic; wiring real open datasets (GEM, Copernicus) is the next
milestone. The tool produces a **pre-design brief** — a licensed local engineer
must still sign the final structural calculations.

## Contributing

Adding a country = adding one JSON file (we give you a generator + validator).
See [`CONTRIBUTING.md`](CONTRIBUTING.md). Beginner-friendly issues welcome.

## License

AGPL-3.0 — free to use, study, and adapt; improvements shared back.
Dual licensing available for agencies needing other terms (see CONTRIBUTING).

<p align="center"><img src="assets/logo.png" alt="OpenShelter logo" width="80"/></p>
