/* OpenShelter live demo controller, engine in briefgen.js, Leaflet self-hosted */
(async () => {
 const $ = id => document.getElementById(id);
 const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
 const ok = await loadHazardGrids();
 $('datastatus').innerHTML = ok
 ? "<b class='ok'>Real data:</b> Earthquake &amp; storm scores are computed live from <b>real public records</b> (USGS earthquake catalogue + NOAA storm history)." 
 : 'Map data not loaded, showing clearly-marked sample values instead.';

 /* ---- interactive hazard map (progressive enhancement) ---- */
 let mapMarker = null;
 function initMap() {
 if (typeof L === 'undefined') return;
 const map = L.map('hzmap', { scrollWheelZoom: false, worldCopyJump: true }).setView([20, 15], 2);
 const light = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { maxZoom: 12, attribution: '&copy; OpenStreetMap &copy; CARTO' });
 const dark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { maxZoom: 12, attribution: '&copy; OpenStreetMap &copy; CARTO' });
 const which = () => (document.documentElement.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light')) === 'dark' ? dark : light;
 which().addTo(map);
 document.addEventListener('click', e => { if (e.target.closest('.theme-toggle')) { map.eachLayer(l => l._url && map.removeLayer(l)); which().addTo(map); } });
 PRESETS.forEach(p => L.circleMarker([+p[1].split(',')[0], +p[1].split(',')[1]], { radius: 6, color: '#0b6e66', weight: 2, fillColor: '#3ec9b0', fillOpacity: .8 })
 .bindTooltip(`${p[0]}, click to see a safety plan`, { direction: 'top' })
 .on('click', () => pickSite(p[1]))
 .addTo(map));
 map.on('click', ev => pickSite(`${ev.latlng.lat.toFixed(2)},${ev.latlng.lng.toFixed(2)}`));
 mapMarker = L.marker([23.81, 90.41], { opacity: .95 }).addTo(map).bindPopup('Your chosen spot');
 $('maphint').style.display = 'block';
 }
 function moveMarker(lat, lon) { if (mapMarker) mapMarker.setLatLng([lat, lon]).openPopup(); }

 function pickSite(val) {
 const [la, lo] = val.split(',');
 $('lat').value = la; $('lon').value = lo;
 $('f').requestSubmit();
 document.getElementById('demo').scrollIntoView({ behavior: 'smooth', block: 'start' });
 }
 $('preset').addEventListener('change', e => { if (e.target.value) pickSite(e.target.value); });

 /* ---- danger-level bars ---- */
 const HZ_NAME = { earthquake: 'Earthquakes', cyclone: 'Storms &amp; cyclones', flood: 'Flooding', heatwave: 'Extreme heat', drought: 'Drought', landslide: 'Landslides' };
 const SRC_TAG = { earthquake: 'real data', cyclone: 'real data', flood: 'sample value', heatwave: 'sample value', drought: 'sample value', landslide: 'sample value' };
 function hzBars(hz) {
 return `<div class="hzbars">${Object.entries(hz).sort((a, z) => z[1] - a[1]).map(([k, v]) => {
 const real = (k === 'earthquake' || k === 'cyclone') && GRID_EQ && GRID_CY;
 return `<div class="hzbar ${real ? 'real' : ''}"><span>${HZ_NAME[k] || esc(k)}</span><span class="track"><span class="fill" style="display:block;width:${Math.round(v * 100)}%"></span></span><span>${Math.round(v * 100)}/100 · ${SRC_TAG[k] || 'sample value'}</span></div>`;
 }).join('')}</div>
 <div class="legend"><span><i style="background:linear-gradient(90deg,var(--brand),#118AB2)"></i>calculated from real public records</span><span><i style="background:var(--brand);opacity:.45"></i>sample value, clearly marked until official data arrives</span></div>`;
 }

 /* ---- form → brief ---- */
 $('f').addEventListener('submit', async e => {
 e.preventDefault();
 const lat = parseFloat($('lat').value), lon = parseFloat($('lon').value);
 const out = $('out');
 out.innerHTML = '<p class="hint">Creating your plan…</p>';
 try {
 const site = { lat, lon, elevation_m: 0, distance_to_water_m: parseFloat($('water').value) || 5000,
 soil_bearing_kpa: 150, population_served: parseInt($('pop').value) || 0,
 hazards: susceptibility(lat, lon, true) };
 const b = await generateBrief(site, $('code').value);
 moveMarker(lat, lon);
 const share = `${location.origin}${location.pathname}#site=${lat},${lon}&code=${$('code').value}`;
 const HZ_LABEL = { earthquake: 'earthquake risk', cyclone: 'storm risk', flood: 'flood risk', heatwave: 'extreme heat', drought: 'drought risk', landslide: 'landslide risk' };
 const PRI_LABEL = { 1: 'MUST DO', 2: 'SHOULD DO', 3: 'GOOD TO DO' };
 const expWord = b.exposure >= 0.66 ? 'high' : b.exposure >= 0.33 ? 'medium' : 'low';
 out.innerHTML = `
 <div class="result-head"><h3>Safety plan. ${lat.toFixed(2)}, ${lon.toFixed(2)}</h3>
 <span class="badge p1">biggest risk: ${HZ_LABEL[b.dominant_hazard] || esc(b.dominant_hazard)}</span>
 <span class="badge p3">overall exposure: ${expWord}</span></div>
 <p class="prov">Where the numbers come from: ${esc(b.meta.hazard_source)} · rulebook: ${esc(b.meta.code_profile)} · tool version ${esc(b.meta.engine_version || '0.2')}, type the same details again and you'll always get this exact plan.</p>
 <p><b>Suggested build type:</b> ${esc(b.structural_system)}</p>
 <p style="font-size:.9rem;margin-bottom:.2rem"><b>Danger levels at this spot (0-100)</b></p>
 ${hzBars(site.hazards)}
 <p>${b.compliance_checks.map(c => `<span class="badge ${c.status === 'PASS' ? 'pass' : c.status === 'NOT-APPLICABLE' ? 'p3' : 'review'}" title="${esc(c.description || '')}">${esc(c.id)}: ${c.status === 'PASS' ? 'Passes' : c.status === 'REVIEW' ? '! needs review' : ' - n/a'}</span>`).join(' ')}</p>
 <ul class="recs">${b.recommendations.map(r => `<li><span class="badge p${r.priority}">${PRI_LABEL[r.priority] || ('P' + r.priority)}</span><b>${esc(r.measure)}</b><em>Why: ${esc(r.reason)}</em></li>`).join('')}</ul>
 <p style="display:flex;gap:.6rem;flex-wrap:wrap">
 <button class="go" style="width:auto;padding:.6rem 1.4rem" onclick="window.print()">Print / save as PDF</button>
 <a class="btn btn-outline btn-sm" href="${share}" rel="noopener">Copy share link</a>
 <button class="btn btn-outline btn-sm" onclick="navigator.clipboard&&navigator.clipboard.writeText('${share}');this.textContent='Link copied'">Share this plan</button>
 </p>`;
 } catch (err) { out.innerHTML = `<p style="color:var(--bad)">Error: ${esc(err.message)}</p>`; }
 });

 initMap();

 /* ---- deep link: #site=lat,lon&code=profile ---- */
 const m = location.hash.match(/site=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(&code=([\w.-]+))?/);
 if (m) {
 $('lat').value = m[1]; $('lon').value = m[2];
 if (m[4]) $('code').value = m[4];
 $('f').requestSubmit();
 }
})();
