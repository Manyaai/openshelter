"""openshelter command-line interface (stdlib argparse, zero extra deps).

Usage examples
--------------
  openshelter codes
  openshelter brief --lat 10.5 --lon 123.9 --code ph-nscc --outdir out
  openshelter batch sites.csv --code sphere-humanitarian --outdir out
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from ..core.codes import CodeRegistry
from ..core.hazard import SiteProfile, exposure_score, dominant_hazard
from ..core.engine import generate_brief
from ..report.generators import write_outputs, to_json


def _cmd_codes(args: argparse.Namespace) -> int:
    reg = CodeRegistry()
    for cid in reg.ids():
        p = reg.get(cid)
        print(f"{cid:24s} {p.jurisdiction:6s} pga>={p.min_pga_g:.2f}g "
              f"wind>={p.wind_speed_kmh:.0f}km/h flood_rp={p.flood_return_period_yr or '-':>3} "
              f"| {p.name}")
    return 0


def _make_site(args: argparse.Namespace) -> SiteProfile:
    return SiteProfile.from_location(
        lat=args.lat, lon=args.lon,
        elevation_m=args.elevation, distance_to_water_m=args.water_distance,
        soil_bearing_kpa=args.soil, population_served=args.population)


def _cmd_brief(args: argparse.Namespace) -> int:
    reg = CodeRegistry()
    code = reg.get(args.code)
    site = _make_site(args)
    brief = generate_brief(site, code)

    if args.format == "json":
        print(to_json(brief))
    else:
        stem = args.stem or f"brief_{abs(site.lat):.2f}_{abs(site.lon):.2f}".replace(".", "p")
        paths = write_outputs(brief, Path(args.outdir), stem=stem)
        for fmt, p in paths.items():
            print(f"[{fmt}] {p}")
        crit = len(brief.critical())
        failed = sum(1 for c in brief.compliance_checks if not c["passed"])
        print(f"\nSite {site.lat:.2f},{site.lon:.2f}: dominant hazard={dominant_hazard(site)}, "
              f"exposure={exposure_score(site):.2f}, critical measures={crit}, "
              f"checks needing review={failed}/{len(brief.compliance_checks)}")
    return 0


def _cmd_batch(args: argparse.Namespace) -> int:
    """Read CSV with columns lat,lon[,elevation,distance_to_water_m,soil_bearing_kpa,population_served]."""
    reg = CodeRegistry()
    code = reg.get(args.code)
    outdir = Path(args.outdir)
    summary = []
    with open(args.sites_csv, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            site = SiteProfile.from_location(
                lat=float(row["lat"]), lon=float(row["lon"]),
                elevation_m=float(row.get("elevation_m", 0) or 0),
                distance_to_water_m=float(row.get("distance_to_water_m", 5000) or 5000),
                soil_bearing_kpa=float(row.get("soil_bearing_kpa", 150) or 150),
                population_served=int(row.get("population_served", 5000) or 5000))
            brief = generate_brief(site, code)
            stem = f"site_{row['lat'].replace('.', 'p')}_{row['lon'].replace('.', 'p')}"
            write_outputs(brief, outdir, stem=stem)
            summary.append({
                "lat": site.lat, "lon": site.lon,
                "dominant_hazard": dominant_hazard(site),
                "exposure": exposure_score(site),
                "critical_measures": len(brief.critical()),
                "structural_system": brief.structural_system,
            })
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {len(summary)} briefs + summary.json to {outdir}/")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="openshelter",
                                 description="Open-source multi-hazard resilient shelter design advisor")
    sub = ap.add_subparsers(dest="command", required=True)

    p_codes = sub.add_parser("codes", help="list available building-code profiles")
    p_codes.set_defaults(func=_cmd_codes)

    p_brief = sub.add_parser("brief", help="generate a design brief for one site")
    p_brief.add_argument("--lat", type=float, required=True)
    p_brief.add_argument("--lon", type=float, required=True)
    p_brief.add_argument("--code", required=True, help="code profile id (see `openshelter codes`)")
    p_brief.add_argument("--elevation", type=float, default=0.0)
    p_brief.add_argument("--water-distance", type=float, default=5000.0)
    p_brief.add_argument("--soil", type=float, default=150.0)
    p_brief.add_argument("--population", type=int, default=5000)
    p_brief.add_argument("--format", choices=["report", "json"], default="report")
    p_brief.add_argument("--outdir", default="out")
    p_brief.add_argument("--stem", default=None)
    p_brief.set_defaults(func=_cmd_brief)

    p_batch = sub.add_parser("batch", help="generate briefs for many sites from a CSV")
    p_batch.add_argument("sites_csv")
    p_batch.add_argument("--code", required=True)
    p_batch.add_argument("--outdir", default="out")
    p_batch.set_defaults(func=_cmd_batch)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
