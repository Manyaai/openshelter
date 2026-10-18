import json
from openshelter.core.codes import CodeRegistry


def test_registry_loads_shipped_profiles():
    reg = CodeRegistry()
    ids = reg.ids()
    assert "eu-eurocode-8" in ids and "sphere-humanitarian" in ids
    assert len(ids) >= 5


def test_profile_fields_valid():
    reg = CodeRegistry()
    for cid in reg.ids():
        p = reg.get(cid)
        assert 0.0 <= p.min_pga_g <= 1.0
        assert p.wind_speed_kmh >= 0
        assert p.standards, f"{cid} must cite at least one real standard"


def test_for_jurisdiction():
    reg = CodeRegistry()
    assert any(p.id == "in-is139-is4352" for p in reg.for_jurisdiction("IN"))


def test_unknown_code_raises_with_hint():
    reg = CodeRegistry()
    try:
        reg.get("nope")
        assert False
    except KeyError as e:
        assert "Available" in str(e)
