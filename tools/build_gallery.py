"""Build the static brief gallery under site/briefs/ from examples/sites.csv."""
from pathlib import Path
import sys, json

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from openshelter.core.hazard import SiteProfile, dominant_hazard, exposure_score
from openshelter.core.codes import CodeRegistry
from openshelter.core.engine import generate_brief
from openshelter.report.generators import to_html

SITES = [
    ("Dhaka, Bangladesh", 23.81, 90.39, "in-is139-is4352", 4, 1200, 80, 10000),
    ("Manila, Philippines", 14.60, 120.98, "ph-nscc", 10, 800, 120, 8000),
    ("Istanbul, Türkiye", 41.01, 28.98, "eu-eurocode-8", 40, 2000, 150, 20000),
    ("Port-au-Prince, Haiti", 18.54, -72.34, "us-iebc", 5, 500, 90, 6000),
    ("Cox's Bazar camp, Bangladesh", 21.43, 92.00, "sphere-humanitarian", 6, 300, 70, 40000),
]

def main() -> int:
    reg = CodeRegistry()
    outdir = Path(__file__).resolve().parent.parent / "site" / "briefs"
    outdir.mkdir(parents=True, exist_ok=True)
    index = []
    for name, lat, lon, code_id, elev, water, soil, pop in SITES:
        site = SiteProfile.from_location(lat=lat, lon=lon, elevation_m=elev,
                                         distance_to_water_m=water, soil_bearing_kpa=soil,
                                         population_served=pop)
        brief = generate_brief(site, reg.get(code_id))
        slug = name.lower().replace("'s", "s").replace(",", "").replace(" ", "-")
        (outdir / f"{slug}.html").write_text(to_html(brief), encoding="utf-8")
        index.append({"name": name, "file": f"{slug}.html", "code": code_id,
                      "dominant_hazard": dominant_hazard(site),
                      "exposure": exposure_score(site),
                      "critical": len(brief.critical())})
    (outdir / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Brief gallery — OpenShelter</title>
<style>body{{font-family:system-ui;margin:2rem auto;max-width:760px;color:#0e2a33;line-height:1.5;padding:0 1rem}}
a{{color:#0f766e;font-weight:600}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:.5rem .7rem;text-align:left}}
tr:nth-child(even){{background:#fafaf7}}</style></head><body>
<h1>📋 Sample design briefs</h1>
<p>Real end-to-end outputs of OpenShelter v0.1 for five high-risk locations. Each brief is fully self-contained and printable.
<em>Demo hazard field is synthetic — see <a href="../">the live demo</a>.</em></p>
<table><tr><th>Location</th><th>Code profile</th><th>Dominant hazard</th><th>Exposure</th><th>Critical measures</th><th>Brief</th></tr>
{"".join(f'<tr><td>{i["name"]}</td><td>{i["code"]}</td><td>{i["dominant_hazard"]}</td><td>{i["exposure"]}</td><td>{i["critical"]}</td><td><a href="{i["file"]}">open →</a></td></tr>' for i in index)}
</table><p><a href="../">← back to OpenShelter home</a></p></body></html>""", encoding="utf-8")
    print(json.dumps(index, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
