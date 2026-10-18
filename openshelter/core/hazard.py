"""Hazard layer: multi-hazard exposure scoring for any point on Earth.

This module is deliberately dependency-free (stdlib only) so it can run
on a Raspberry Pi in the field, inside a national data centre, or in a
browser via Pyodide.  It combines openly licensed global datasets
(GEM hazard layers, Copernicus land cover, FAO soil grids, etc.) into a
transparent, versioned "hazard fingerprint" for a given location.

The scores are intentionally simple, deterministic and auditable —
governments need to be able to reproduce every number in a public
procurement or subsidy decision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List


# ---------------------------------------------------------------------------
# Hazard model
# ---------------------------------------------------------------------------
# Each hazard has a base susceptibility (0..1) that would come from a real
# global raster layer in production.  Here we expose a pluggable provider
# interface so national agencies can swap in their own authoritative data.

HAZARD_NAMES = [
    "flood",
    "earthquake",
    "cyclone",
    "heatwave",
    "drought",
    "landslide",
]


class HazardProvider:
    """Interface for hazard susceptibility providers.

    Implementations read from authoritative rasters (GeoTIFF, WMS, tile
    services such as the GEM Risk Library or Copernicus EMS) and return
    per-hazard susceptibility values in [0, 1].
    """

    def susceptibility(self, lat: float, lon: float) -> Dict[str, float]:
        raise NotImplementedError


@dataclass
class SyntheticHazardProvider(HazardProvider):
    """Deterministic pseudo-hazard model used for demos and tests.

    NOT for operational decisions.  It exists so the whole pipeline can be
    exercised end-to-end without network access.  Replace it with a real
    raster-backed provider (see ``openshelter.providers.gem`` once
    implemented) before any public-sector deployment.
    """

    def susceptibility(self, lat: float, lon: float) -> Dict[str, float]:
        # Smooth pseudo-random fields derived from coordinates.
        def wave(phase: float) -> float:
            return 0.5 + 0.5 * math.sin(math.radians(lat * 3 + phase) +
                                        math.cos(math.radians(lon * 2 + phase)))

        flood = wave(0.0) * (1.0 if abs(lat) < 66 else 0.2)
        earthquake = wave(90.0) * self._plate_boundary_factor(lat, lon)
        cyclone = wave(180.0) if 5 <= abs(lat) <= 30 else 0.05
        heatwave = max(0.0, 1.0 - abs(abs(lat) - 25) / 25.0) * wave(45.0)
        drought = wave(270.0) if 15 <= abs(lat) <= 40 else 0.1
        landslide = wave(135.0) * 0.6

        return {
            "flood": round(min(flood, 1.0), 3),
            "earthquake": round(min(earthquake, 1.0), 3),
            "cyclone": round(min(cyclone, 1.0), 3),
            "heatwave": round(min(heatwave, 1.0), 3),
            "drought": round(min(drought, 1.0), 3),
            "landslide": round(min(landslide, 1.0), 3),
        }

    @staticmethod
    def _plate_boundary_factor(lat: float, lon: float) -> float:
        # Crude approximation: proximity to the Pacific Ring of Fire axes.
        ring = abs(abs(lon) - 170) / 170.0
        return max(0.2, 1.0 - ring)


@dataclass
class SiteProfile:
    """Physical description of a candidate site."""

    lat: float
    lon: float
    elevation_m: float = 0.0
    distance_to_water_m: float = 5000.0   # river/coast
    soil_bearing_kpa: float = 150.0
    population_served: int = 5000
    hazards: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (-90.0 <= self.lat <= 90.0 and -180.0 <= self.lon <= 180.0):
            raise ValueError("lat/lon out of range")

    @classmethod
    def from_location(cls, lat: float, lon: float, provider: HazardProvider | None = None,
                      **kwargs) -> "SiteProfile":
        provider = provider or SyntheticHazardProvider()
        profile = cls(lat=lat, lon=lon, **kwargs)
        profile.hazards = provider.susceptibility(lat, lon)
        return profile

    def to_dict(self) -> dict:
        return asdict(self)


def dominant_hazard(profile: SiteProfile) -> str:
    if not profile.hazards:
        return "none"
    return max(profile.hazards.items(), key=lambda kv: kv[1])[0]


def exposure_score(profile: SiteProfile) -> float:
    """Aggregate exposure 0..1 (weighted by consequence severity)."""
    weights = {"flood": 1.0, "earthquake": 1.2, "cyclone": 1.0,
               "heatwave": 0.7, "drought": 0.6, "landslide": 0.9}
    total_w = sum(weights.values())
    score = sum(profile.hazards.get(h, 0.0) * w for h, w in weights.items())
    return round(score / total_w, 3)
