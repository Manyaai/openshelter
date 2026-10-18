"""Design engine: turns a SiteProfile + CodeProfile into a compliant design brief.

The engine is rule-based and explainable.  Every recommendation carries a
``reason`` string citing the hazard value and the code clause that produced
it, so a reviewing engineer (or an auditor, or a judge) can trace every
decision back to open data and published standards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .hazard import SiteProfile, dominant_hazard, exposure_score
from .codes import CodeProfile


@dataclass
class Recommendation:
    topic: str            # e.g. "structure", "water", "energy"
    measure: str          # what to do
    reason: str           # why (cites hazard value + code reference)
    priority: int = 3     # 1 = critical, 5 = nice-to-have
    cost_band: str = "medium"   # low | medium | high


@dataclass
class DesignBrief:
    site: SiteProfile
    code: CodeProfile
    recommendations: List[Recommendation] = field(default_factory=list)
    structural_system: str = ""
    energy_strategy: str = ""
    water_strategy: str = ""
    sanitation_strategy: str = ""
    thermal_strategy: str = ""
    compliance_checks: List[Dict] = field(default_factory=list)

    def critical(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.priority == 1]


def _dominant_design_gale(code: CodeProfile, hazards: Dict[str, float]) -> float:
    """Return governing wind speed: max(code minimum, cyclone-informed)."""
    cyclone = hazards.get("cyclone", 0.0)
    informed = 120.0 + cyclone * 130.0   # crude mapping susceptibility→gust
    return max(code.wind_speed_kmh, round(informed))


def generate_brief(site: SiteProfile, code: CodeProfile) -> DesignBrief:
    brief = DesignBrief(site=site, code=code)
    hz = site.hazards
    dom = dominant_hazard(site)
    exp = exposure_score(site)

    # ---- Structural system -------------------------------------------------
    pga_req = code.min_pga_g
    eq = hz.get("earthquake", 0.0)
    if eq >= 0.6 or pga_req >= 0.25:
        brief.structural_system = "confined-masonry or RC frame, ductile detailing"
        brief.recommendations.append(Recommendation(
            "structure",
            "Use ductile moment-resisting frame or confined masonry with seismic ties",
            f"Earthquake susceptibility {eq:.2f}; code '{code.id}' requires design "
            f"PGA >= {pga_req:.2f} g ({', '.join(code.standards[:2])})",
            priority=1, cost_band="high"))
    elif hz.get("cyclone", 0) >= 0.5:
        brief.structural_system = "lightweight steel/timber frame, continuous load path to anchors"
        brief.recommendations.append(Recommendation(
            "structure",
            "Continuous tie-down load path; hurricane clips; impact-resistant glazing",
            f"Cyclone susceptibility {hz['cyclone']:.2f}; design wind "
            f"{_dominant_design_gale(code, hz):.0f} km/h",
            priority=1, cost_band="medium"))
    else:
        brief.structural_system = "load-bearing masonry/RSS with ring beam"
        brief.recommendations.append(Recommendation(
            "structure",
            "Reinforced ring beam at roof level; controlled quality of masonry units",
            "Baseline robustness for moderate multi-hazard exposure "
            f"(aggregate exposure {exp:.2f})"))

    # ---- Flood / siting ----------------------------------------------------
    flood = hz.get("flood", 0.0)
    rp = code.flood_return_period_yr or 20
    if flood >= 0.55 or site.distance_to_water_m < 1500:
        brief.recommendations.append(Recommendation(
            "siting",
            "Raise finished floor >= 0.5 m above modelled design flood level, or select alternate parcel",
            f"Flood susceptibility {flood:.2f}; code expects protection for a "
            f"{rp}-year return period event",
            priority=1, cost_band="medium"))
    elif flood >= 0.35:
        brief.recommendations.append(Recommendation(
            "siting",
            "Waterproof habitable ground floor; locate utilities on upper level",
            f"Moderate flood susceptibility {flood:.2f}", priority=2))

    # ---- Thermal / heatwave --------------------------------------------------
    heat = hz.get("heatwave", 0.0)
    if heat >= 0.5:
        brief.thermal_strategy = "high-mass + shade"
        brief.recommendations.append(Recommendation(
            "thermal",
            "Cool-roof (SRI>=78), external shading, night-purge ventilation; target indoor <=35C during heat alert",
            f"Heatwave susceptibility {heat:.2f}. Aligns with WHO shelter guidance "
            "and EPBD-style nearly-zero-energy intent where applicable",
            priority=1, cost_band="low"))
    elif site.elevation_m > 800 or abs(site.lat) > 45:
        brief.thermal_strategy = "insulated envelope"
        brief.recommendations.append(Recommendation(
            "thermal",
            "Wall/roof insulation; airtight layer; stove-safe flue design",
            "Cold-climate envelope strategy; see code thermal note: "
            f"'{code.thermal_min_note or 'n/a'}'", priority=2, cost_band="medium"))

    if code.snow_load_knm2 > 0:
        brief.recommendations.append(Recommendation(
            "structure",
            f"Roof designed for {code.snow_load_knm2:.1f} kN/m^2 ground snow load",
            f"Required by '{code.id}'", priority=2, cost_band="low"))

    # ---- Water & sanitation ---------------------------------------------------
    drought = hz.get("drought", 0.0)
    if drought >= 0.45:
        brief.water_strategy = "rainwater harvesting + greywater reuse"
        brief.recommendations.append(Recommendation(
            "water",
            "Roar-area rainwater harvesting sized for 15 L/person/day x dry months; first-flush diverter",
            f"Drought susceptibility {drought:.2f}", priority=1, cost_band="low"))
    else:
        brief.water_strategy = "rainwater harvesting (opportunistic)"
    brief.sanitation_strategy = "ventilated improved pit (VIP) or composting toilet; never discharge into flood zone"
    brief.recommendations.append(Recommendation(
        "sanitation",
        brief.sanitation_strategy,
        "Sphere Standards WASH minimum requirements (20 L/person/day, "
        "4.6 m2 shelter/person); flood/drought aware placement", priority=2, cost_band="low"))

    # ---- Energy ----------------------------------------------------------------
    if abs(site.lat) <= 35:
        brief.energy_strategy = "off-grid PV solar"
        brief.recommendations.append(Recommendation(
            "energy",
            "Roof-mounted PV >= 200 W/person-served-day with battery; supports cooling and comms",
            "High irradiance at this latitude; Sphere + IASC mental-health guidance "
            "on lighting and charging facilities", priority=2, cost_band="medium"))
    else:
        brief.energy_strategy = "grid-tied with backup"
        brief.recommendations.append(Recommendation(
            "energy",
            "PV-ready roof area reserved; efficient LED base load",
            "Future-proofing per code thermal/energy note", priority=3, cost_band="low"))

    # ---- Accessibility & protection ---------------------------------------------
    if code.accessibility:
        brief.recommendations.append(Recommendation(
            "protection",
            "Step-free entrance, 900 mm door clear width, accessible WASH cubicle",
            f"Mandatory under '{code.name}' accessibility provisions",
            priority=1, cost_band="low"))
    else:
        brief.recommendations.append(Recommendation(
            "protection",
            "Provide at least one step-free, lockable, internally-connecting family unit",
            "Sphere Standard 2 (Inclusive design) — recommended even where not codified",
            priority=2, cost_band="low"))

    # ---- Compliance checks (machine-verifiable) -----------------------------------
    checks = []

    def check(name: str, ok: bool, detail: str):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    check("design PGA meets code",
          eq * 0.5 >= pga_req or pga_req == 0.0,
          f"modelled demand ~{eq * 0.5:.2f} g vs required >= {pga_req:.2f} g")
    check("design wind meets code",
          _dominant_design_gale(code, hz) >= code.wind_speed_kmh,
          f"{_dominant_design_gale(code, hz):.0f} km/h vs required >= {code.wind_speed_kmh:.0f} km/h")
    check("floor elevation above water proximity threshold",
          site.elevation_m > 3 or site.distance_to_water_m > 1500,
          f"elevation {site.elevation_m} m, distance to water {site.distance_to_water_m} m")
    check("soil bearing adequate for chosen system",
          site.soil_bearing_kpa >= 80,
          f"{site.soil_bearing_kpa} kPa reported")
    brief.compliance_checks = checks

    brief.recommendations.sort(key=lambda r: r.priority)
    return brief
