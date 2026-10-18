/* OpenShelter live demo controller (uses briefgen.js engine port) */
(async () => {
  const $ = id => document.getElementById(id);
  const ok = await loadHazardGrids();
  $('datastatus').innerHTML = ok
    ? '✅ Earthquake &amp; cyclone scores computed live from <b>real public-domain grids</b> (USGS ComCat + NOAA IBTrACS).'
    : '⚠️ Hazard grids unavailable offline — falling back to the labelled synthetic demo field.';

  $('preset').addEventListener('change', e => {
    if (!e.target.value) return;
    const [la, lo] = e.target.value.split(',');
    $('lat').value = la; $('lon').value = lo;
    $('f').requestSubmit(); // instant gratification: generate on pick
  });

  $('f').addEventListener('submit', async e => {
    e.preventDefault();
    const lat = parseFloat($('lat').value), lon = parseFloat($('lon').value);
    const out = $('out');
    out.innerHTML = '<p class="hint">Generating brief…</p>';
    try {
      const site = { lat, lon, elevation_m: 0, distance_to_water_m: parseFloat($('water').value) || 5000,
        soil_bearing_kpa: 150, population_served: parseInt($('pop').value) || 0,
        hazards: susceptibility(lat, lon, true) };
      const b = await generateBrief(site, $('code').value);
      const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
      const hz = Object.entries(site.hazards).sort((a, z) => z[1] - a[1]);
      out.innerHTML = `
        <div class="result-head"><h3>Design brief — ${lat.toFixed(2)}, ${lon.toFixed(2)}</h3>
          <span class="badge p1">dominant: ${esc(b.dominant_hazard)}</span>
          <span class="badge p3">exposure ${b.exposure}</span></div>
        <p class="prov">🔎 Provenance: ${esc(b.meta.hazard_source)} · code profile <code>${esc(b.meta.code_profile)}</code> · engine v${esc(b.meta.engine_version || '0.2')} — deterministic: same inputs always produce this exact brief.</p>
        <p><b>Suggested structural system:</b> ${esc(b.structural_system)}</p>
        <p style="font-size:.9rem"><b>Hazard fingerprint:</b> ${hz.map(([k, v]) => `${esc(k)} ${v.toFixed(2)}`).join(' · ')}</p>
        <p>${b.compliance_checks.map(c => `<span class="badge ${c.status === 'PASS' ? 'pass' : 'review'}">${esc(c.id)}: ${esc(c.status)}</span>`).join(' ')}</p>
        <ul class="recs">${b.recommendations.map(r => `<li><span class="badge p${r.priority}">P${r.priority}</span><b>${esc(r.measure)}</b><em>Why: ${esc(r.reason)}</em></li>`).join('')}</ul>
        <p><button class="go" style="width:auto;padding:.6rem 1.4rem" onclick="window.print()">🖨 Print / save this brief as PDF</button></p>`;
    } catch (err) { out.innerHTML = `<p style="color:var(--bad)">Error: ${esc(err.message)}</p>`; }
  });
})();
