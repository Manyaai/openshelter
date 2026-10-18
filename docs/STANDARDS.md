# Standards & data provenance

Every number OpenShelter outputs must be traceable to a published, citable source.

## Building-code profiles (openshelter/data/codes/)
| Profile id | Real-world sources |
|---|---|
| eu-eurocode-8 | EN 1998-1 (Eurocode 8), EN 1991-1-3/1-4 (snow/wind), Directive (EU) 2024/3100 (EPBD recast, zero-emission buildings from 2030/2033) |
| us-iebc | ICC International Building Code 2024 (Group R emergency shelters), ASCE 7-22, FEMA P-361 (safe room criteria), ADA Standards for Accessible Design |
| in-is139-is4352 | IS 13932:2016 (cyclone-resistant buildings), IS 1893-1:2016 + IS 4352 (earthquake), IS 875 parts 1-3 (loads), ECBC 2017, CPHEEO water supply manual |
| ph-nscc | National Structural Code of the Philippines 2015 Vol.1, DPWH typhoon-resilient house construction manuals, ZNOS storm-surge guidance |
| sphere-humanitarian | Sphere Handbook 2018 (Shelter & Settlements, WASH), IASC Guidelines on Mental Health and Psychosocial Support, UNHCR emergency shelter standards |

Values in shipped profiles are **conservative minima for demonstration**.
National agencies should replace them with jurisdiction-specific annexes via PR.

## Hazard layers (target providers)
- GEM Foundation Risk Library / Global Risk Patterns (open data)
- Copernicus EMS flood hazard rasters, ERA5 heat variables
- FAO SoilGrids (soil bearing proxies), SRTM/Copernicus DEM (elevation)
- Jaha/Natural Earth for exposure; national met agencies where available

## Humanitarian design thresholds encoded in the engine
- 4.6 m2 covered living space/person (warm climates); 3.5 m2 open space/person (Sphere)
- 15 L/person/day minimum water in extremis, 20 L typical (Sphere WASH)
- Thermal comfort band 18-30 C habitations; >=2 air changes/hour (Sphere Indicator 1)
- Cool roof SRI >= 78 for heatwave sites (WHO cold-weather/heat guidance lineage)

## Licence compatibility
All cited datasets above are CC-BY / open-government or similar; profiles carry
their own `notes` field recording any jurisdiction-specific redistribution limits.
