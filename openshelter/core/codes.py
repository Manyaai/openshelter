"""Building-code and standards registry.

The compliance layer is a *registry*, not a hard-coded rulebook: each
jurisdiction's requirements are declarative JSON profiles that local
authorities can maintain themselves (and that OpenShelter validates).
This is what makes the project sustainable — the software stays generic,
the legal content belongs to (and is funded by) the public body that owns
the code.

Profiles reference real standards; see docs/STANDARDS.md for sources.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class CodeProfile:
    """A machine-readable extract of a national/regional building code."""

    id: str                                   # e.g. "eu-eurocode-8"
    name: str                                 # human readable
    jurisdiction: str                         # ISO 3166 country or region code
    standards: List[str] = field(default_factory=list)   # canonical standard refs
    min_pga_g: float = 0.0                    # design ground acceleration
    wind_speed_kmh: float = 0.0               # design basic wind speed
    flood_return_period_yr: int = 0           # 0 = no fluvial requirement
    snow_load_knm2: float = 0.0
    thermal_min_note: str = ""                # e.g. "nZEB per EPBD recast"
    accessibility: bool = False               # mandatory accessibility reqs
    notes: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "CodeProfile":
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in allowed})


class CodeRegistry:
    """Loads all JSON code profiles shipped under openshelter/data/codes/."""

    def __init__(self, codes_dir: Optional[Path] = None) -> None:
        self._dir = codes_dir or (DATA_DIR / "codes")
        self._profiles: Dict[str, CodeProfile] = {}
        self.reload()

    def reload(self) -> None:
        self._profiles.clear()
        if not self._dir.is_dir():
            raise FileNotFoundError(f"codes directory missing: {self._dir}")
        for p in sorted(self._dir.glob("*.json")):
            profile = CodeProfile.from_dict(json.loads(p.read_text()))
            self._profiles[profile.id] = profile

    def ids(self) -> List[str]:
        return sorted(self._profiles)

    def get(self, code_id: str) -> CodeProfile:
        if code_id not in self._profiles:
            raise KeyError(
                f"unknown code '{code_id}'. Available: {', '.join(self.ids())}"
            )
        return self._profiles[code_id]

    def for_jurisdiction(self, iso_code: str) -> List[CodeProfile]:
        iso = iso_code.lower()
        return [p for p in self._profiles.values() if p.jurisdiction.startswith(iso)]
