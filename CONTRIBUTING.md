# Contributing

## Add a country building code (the highest-leverage contribution)
```bash
python tools/new_code_profile.py --id mx-cfe --name "CFE 2023 Mexico" --jurisdiction mx
# edit openshelter/data/codes/mx-cfe.json, then:
python tools/new_code_profile.py --check
python -m pytest tests/
```
Rules: cite real standard identifiers in `standards`; keep numeric fields
conservative; put caveats in `notes`. The profile owner (authority) is listed
in the PR description.

## Engine rules
Every new Recommendation MUST carry a `reason` string citing (a) the hazard
value or site parameter and (b) the code/standard reference. No rule without
provenance is merged.

## Tests
Core stays stdlib-only. All tests must run offline and be deterministic
(same input → byte-identical JSON).
