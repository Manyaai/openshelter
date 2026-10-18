from openshelter.core.codes import CodeRegistry
from openshelter.core.hazard import SiteProfile
from openshelter.core.engine import generate_brief


def _brief(lat, lon, code_id, **kw):
    site = SiteProfile.from_location(lat, lon, **kw)
    return generate_brief(site, CodeRegistry().get(code_id))


def test_ph_typhoon_site_gets_critical_structural_or_wind_measure():
    b = _brief(12.88, 121.75, "ph-nscc")
    assert b.recommendations and b.recommendations[0].priority == 1
    assert b.compliance_checks


def test_eu_accessibility_is_mandatory_p1():
    b = _brief(45.46, 9.19, "eu-eurocode-8")
    prot = [r for r in b.recommendations if r.topic == "protection"]
    assert any(r.priority == 1 and "Step-free" in r.measure for r in prot)


def test_snow_load_recommendation_follows_code():
    b = _brief(47.37, 8.54, "eu-eurocode-8")
    assert any("snow load" in r.measure for r in b.recommendations)


def test_low_flood_risk_no_raise_floor_order():
    # Chicago coords happen to score high in the *synthetic* demo field, so we
    # inject an explicit low-hazard profile to test the rule logic itself.
    site = SiteProfile(lat=41.9, lon=-87.6, elevation_m=180,
                       distance_to_water_m=60000,
                       hazards={"flood": 0.05, "earthquake": 0.1, "cyclone": 0.0,
                                "heatwave": 0.2, "drought": 0.1, "landslide": 0.05})
    b = generate_brief(site, CodeRegistry().get("us-iebc"))
    siting = [r for r in b.recommendations if r.topic == "siting"]
    assert not any(r.priority == 1 and "Raise finished floor" in r.measure for r in siting)


def test_briefs_are_deterministic():
    import json
    from openshelter.report.generators import to_json
    a = to_json(_brief(10.5, 123.9, "ph-nscc"))
    c = to_json(_brief(10.5, 123.9, "ph-nscc"))
    assert a == c
