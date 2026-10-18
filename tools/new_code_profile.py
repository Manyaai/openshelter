#!/usr/bin/env python3
"""Scaffold and validate building-code profiles.

  python tools/new_code_profile.py --id mx-cfe --name "CFE 2023 Mexico" --jurisdiction mx
  python tools/new_code_profile.py --check          # validate every shipped profile
"""
from __future__ import annotations

import argparse, json, re, sys
from pathlib import Path

CODES_DIR = Path(__file__).resolve().parent.parent / "openshelter" / "data" / "codes"

TEMPLATE = {
    "id": "", "name": "", "jurisdiction": "", "standards": [],
    "min_pga_g": 0.0, "wind_speed_kmh": 0.0, "flood_return_period_yr": 0,
    "snow_load_knm2": 0.0, "thermal_min_note": "", "accessibility": False,
    "notes": "TODO: cite the exact clause numbers you transcribed values from.",
}

def validate(path: Path) -> list[str]:
    errs = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"{path.name}: invalid JSON ({e})"]
    for key in TEMPLATE:
        if key not in d:
            errs.append(f"{path.name}: missing field '{key}'")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", str(d.get("id", ""))):
        errs.append(f"{path.name}: bad id")
    if not d.get("standards"):
        errs.append(f"{path.name}: must cite at least one real standard")
    if not (0 <= float(d.get("min_pga_g", 0)) <= 1):
        errs.append(f"{path.name}: min_pga_g out of range")
    if not (0 <= float(d.get("wind_speed_kmh", 0)) <= 400):
        errs.append(f"{path.name}: wind_speed_kmh out of range")
    if d.get("id") and path.stem != d["id"]:
        errs.append(f"{path.name}: filename must equal id '{d['id']}'")
    return errs

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate all profiles")
    ap.add_argument("--id"); ap.add_argument("--name"); ap.add_argument("--jurisdiction")
    args = ap.parse_args()

    if args.check:
        all_errs = [e for p in sorted(CODES_DIR.glob("*.json")) for e in validate(p)]
        print("\n".join(all_errs) if all_errs else f"OK: {len(list(CODES_DIR.glob('*.json')))} profiles valid")
        return 1 if all_errs else 0

    if not (args.id and args.name and args.jurisdiction):
        ap.error("--id/--name/--jurisdiction are required when scaffolding")
    dest = CODES_DIR / f"{args.id}.json"
    if dest.exists():
        print(f"error: {dest} already exists", file=sys.stderr); return 1
    t = dict(TEMPLATE, id=args.id, name=args.name, jurisdiction=args.jurisdiction.lower())
    dest.write_text(json.dumps(t, indent=2) + "\n", encoding="utf-8")
    print(f"Created {dest}\nFill in conservative minima from the published code, then run: python tools/new_code_profile.py --check")
    return 0

if __name__ == "__main__":
    sys.exit(main())
