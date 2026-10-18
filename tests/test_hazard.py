import pytest
from openshelter.core.hazard import SiteProfile, SyntheticHazardProvider, dominant_hazard, exposure_score


def test_provider_returns_all_hazards():
    hz = SyntheticHazardProvider().susceptibility(10.5, 123.9)
    assert set(hz) == {"flood", "earthquake", "cyclone", "heatwave", "drought", "landslide"}
    assert all(0.0 <= v <= 1.0 for v in hz.values())


def test_provider_is_deterministic():
    p = SyntheticHazardProvider()
    assert p.susceptibility(14.6, -90.5) == p.susceptibility(14.6, -90.5)


def test_invalid_coords_rejected():
    with pytest.raises(ValueError):
        SiteProfile(lat=95.0, lon=0.0)


def test_exposure_and_dominant():
    site = SiteProfile.from_location(21.0, 89.0)  # Ganges delta-ish
    assert dominant_hazard(site) in site.hazards
    assert 0.0 <= exposure_score(site) <= 1.0
