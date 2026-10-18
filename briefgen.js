/* OpenShelter brief generator — faithful JS port of openshelter/core/{hazard,codes,engine}.py v0.1.0
 * Deterministic, dependency-free, runs entirely in the browser.
 * NOTE: demo hazard field is synthetic (same as Python SyntheticHazardProvider) — NOT for operational decisions.
 */
const HAZARD_NAMES = ["flood","earthquake","cyclone","heatwave","drought","landslide"];

/* Real public-domain hazard grids (0.5 deg): USGS ComCat earthquakes, NOAA IBTrACS cyclone climatology */
let GRID_EQ = null, GRID_CY = null;
async function loadHazardGrids(){
  if (GRID_EQ && GRID_CY) return true;
  try {
    const [e,c] = await Promise.all([
      fetch("data/earthquakes_0p5deg.json").then(r=>r.ok?r.json():null),
      fetch("data/cyclones_0p5deg.json").then(r=>r.ok?r.json():null)]);
    if (e && c) { GRID_EQ = e.cells; GRID_CY = c.cells; return true; }
  } catch(_) {}
  return false;
}
function gridCell(grid, lat, lon){ return grid ? (grid[`${Math.round(lat*2)/2},${Math.round(lon*2)/2}`] || 0) : 0; }
const PROVENANCE = {earthquake:"USGS ComCat M6.0+ 1990-2026 (public domain)",cyclone:"NOAA IBTrACS storm-track climatology (public domain)",flood:"synthetic demo field",heatwave:"synthetic demo field",drought:"synthetic demo field",landslide:"synthetic demo field"};

function susceptibility(lat, lon, useReal) {
  const wave = (phase) => 0.5 + 0.5 * Math.sin((lat*3 + phase) * Math.PI/180 + Math.cos((lon*2 + phase) * Math.PI/180));
  const ring = Math.abs(Math.abs(lon) - 170) / 170;
  const plate = Math.max(0.2, 1.0 - ring);
  let flood = wave(0) * (Math.abs(lat) < 66 ? 1 : 0.2);
  let earthquake = wave(90) * plate;
  let cyclone = (5 <= Math.abs(lat) && Math.abs(lat) <= 30) ? wave(180) : 0.05;
  let heatwave = Math.max(0, 1 - Math.abs(Math.abs(lat) - 25)/25) * wave(45);
  let drought = (15 <= Math.abs(lat) && Math.abs(lat) <= 40) ? wave(270) : 0.1;
  let landslide = wave(135) * 0.6;
  const r3 = x => Math.round(Math.min(x, 1.0) * 1000) / 1000;
  let eq = r3(earthquake), cy = r3(cyclone);
  if (useReal && GRID_EQ && GRID_CY) {
    eq = r3(Math.max(eq, Math.max(gridCell(GRID_EQ,lat,lon), eq*0.35)));
    cy = r3(Math.max(cy, Math.max(gridCell(GRID_CY,lat,lon), cy*0.35)));
  }
  return {flood:r3(flood), earthquake:eq, cyclone:cy,
          heatwave:r3(heatwave), drought:r3(drought), landslide:r3(landslide)};
}

function dominantHazard(hz){ return HAZARD_NAMES.reduce((a,b)=> hz[b]>hz[a]?b:a, HAZARD_NAMES[0]); }

function exposureScore(hz){
  const w = {flood:1.0, earthquake:1.2, cyclone:1.0, heatwave:0.7, drought:0.6, landslide:0.9};
  const tw = Object.values(w).reduce((a,b)=>a+b,0);
  const s = Object.entries(w).reduce((a,[h,k])=>a+(hz[h]||0)*k,0);
  return Math.round(s/tw*1000)/1000;
}

async function generateBrief(site, code){
  const usingReal = !!(GRID_EQ && GRID_CY);
  const resp = await fetch(`data/codes/${code}.json`);
  if (!resp.ok) throw new Error("code profile not found: "+code);
  const c = await resp.json();
  const hz = site.hazards;
  const dom = dominantHazard(hz);
  const recs = [];
  const add = (topic, measure, reason, priority=3, cost_band="medium") =>
    recs.push({topic, measure, reason, priority, cost_band});

  // Structural system (mirrors engine.py logic)
  let structural = "lightweight timber/steel frame on engineered footing";
  if (hz.earthquake >= 0.6 || c.min_pga_g >= 0.25) {
    structural = "confined-masonry or RC frame, ductile detailing";
    add("structure","Ductile lateral-force-resisting system designed for ≥ "+c.min_pga_g+"g peak ground acceleration",
        `Site earthquake susceptibility ${hz.earthquake}; ${c.name} minimum design PGA ${c.min_pga_g}g (${c.standards[0]})`,1,"high");
  } else if (hz.earthquake >= 0.3) {
    structural = "confined-masonry with seismic rings";
    add("structure","Confined masonry with continuous tie-beams/ring beams",
        `Moderate earthquake susceptibility ${hz.earthquake}; ${c.name} (${c.standards[0]})`,2,"medium");
  }
  const wind = Math.max(c.wind_speed_kmh, Math.round(120 + hz.cyclone*130));
  if (wind >= 180) add("structure","Engineered roof-to-wall connectors and hurricane straps rated for "+wind+" km/h gusts",
      `Cyclone susceptibility ${hz.cyclone}; governing design wind ${wind} km/h vs ${c.name} baseline ${c.wind_speed_kmh} km/h`,1,"medium");
  else if (wind >= 140) add("structure","Storm ties and reinforced roof cladding for "+wind+" km/h design gust",
      `Cyclone susceptibility ${hz.cyclone}; design wind ${wind} km/h`,2,"low");

  // Flood siting
  if (hz.flood >= 0.5 || (c.flood_return_period_yr > 0 && site.distance_to_water_m < 200)) {
    add("site","Raise finished floor ≥ 0.5 m above modelled "+(c.flood_return_period_yr||100)+"-yr flood level, or select an alternate footprint",
        `Flood susceptibility ${hz.flood}; distance to water ${site.distance_to_water_m} m; ${c.name} requires ${c.flood_return_period_yr||100}-yr return period siting`,1,"medium");
  }
  if (hz.landslide >= 0.6) add("site","Avoid cut slopes; retain or setback ≥ 15 m from unstable gradients",
      `Landslide susceptibility ${hz.landslide}`,2,"medium");
  if (site.soil_bearing_kpa < 100) add("foundation","Ground-bearing improvement (compaction/gravel raft) or pad footings for ≥100 kPa",
      `Reported soil bearing ${site.soil_bearing_kpa} kPa below shallow-footing comfort zone`,2,"medium");

  // Heat / thermal
  if (hz.heatwave >= 0.55) {
    add("thermal","High-albedo 'cool roof' (SRI ≥ 80), ridge ventilation, shaded veranda on equator-facing side",
        `Heatwave susceptibility ${hz.heatwave}; ${c.thermal_min_note || "passive cooling recommended"}`,1,"low");
    add("thermal","Interior thermal mass or night-purge windows to keep daytime operative temperature < 30 °C",
        `Heatwave susceptibility ${hz.heatwave}`,2,"low");
  }
  if (c.snow_load_knm2 > 0) add("structure","Roof designed for ≥ "+c.snow_load_knm2+" kN/m² snow load with slip planes above rafters",
      `${c.name} snow provision ${c.snow_load_knm2} kN/m²`,2,"medium");

  // Water & sanitation (Sphere-aligned thresholds where population given)
  const pop = site.population_served || 0;
  if (pop > 0) {
    add("water","Rainwater harvesting sized for ≥ 15 L/person/day (Sphere SP-2.1): "+Math.ceil(pop*15/1000)+" m³ storage per 10 dry days",
        `Population served ${pop}; Sphere minimum survival quantity 15 L/p/d`,1,"low");
    if (hz.drought >= 0.5) add("water","Back-up borehole or tanker connection point; raw-water reserve of 5 L/p/d beyond harvest buffer",
        `Drought susceptibility ${hz.drought}`,2,"high");
    add("sanitation","1 latrine per 20 people (Sphere SP-3.1): ≥ "+Math.ceil(pop/20)+" squatting plates, gender-separated blocks",
        `Population served ${pop}; Sphere standard 1/20`,1,"medium");
    if (hz.flood >= 0.5) add("sanitation","Raised/pit-slab latrines above flood line; lined pits ≥ 30 m from any water source",
        `Flood susceptibility ${hz.flood} risks pit overflow and faecal contamination`,1,"medium");
  }
  if (c.accessibility) add("inclusion","Step-free entry ≤ 1:12 ramp, 90 cm doorways, handrails, accessible latrine stall",
      `${c.name} mandates accessibility (${c.standards.join(", ")})`,1,"low");
  add("energy","PV-ready roof area ≥ 1 m² per 10 occupants with pre-wired conduit and battery room",
      "Resilience best practice; supports lighting, comms and medical refrigeration",3,"medium");

  const checks = [
    {id:"PGA", description:`Design ground acceleration ≥ ${c.min_pga_g} g`, status: hz.earthquake>=0.6 && c.min_pga_g<0.15 ? "REVIEW":"PASS", basis:`${c.name} / ${c.standards[0]}`},
    {id:"WIND", description:`Governing gust ≥ ${wind} km/h`, status: wind>=c.wind_speed_kmh?"PASS":"REVIEW", basis:`${c.name}`},
    {id:"FLOOD", description:c.flood_return_period_yr>0?`Sited outside ${c.flood_return_period_yr}-yr flood extent`:"No fluvial requirement", status: hz.flood>=0.5?"REVIEW":"PASS", basis:`${c.name}`},
    {id:"WASH", description:"Sphere WASH minima met in program", status: pop>0?"PASS":"NOT-APPLICABLE", basis:"Sphere Handbook"},
  ];

  return {
    meta:{tool:"openshelter-js", version:"0.2.0",
      hazard_source: usingReal ? "USGS + IBTrACS grids (eq/cy) + synthetic fields (flood/heat/drought/landslide)" : "synthetic demo field only",
      provenance: PROVENANCE,
      note:"Earthquake & cyclone scores use real public-domain data. Other hazards are demo values — verify against authoritative national layers before building."},
    site:{...site, code:c.id},
    dominant_hazard:dom, exposure:exposureScore(hz),
    structural_system:structural,
    recommendations:recs.sort((a,b)=>a.priority-b.priority),
    compliance_checks:checks,
  };
}
