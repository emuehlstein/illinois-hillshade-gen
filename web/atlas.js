// atlas.js — Exaggerated Relief county atlas
// Status-driven choropleth + floating drawer UX

const TILES_BASE = 'https://exaggeratedrelief.s3.us-east-2.amazonaws.com';
const IL_CENTER  = [-89.3985, 40.633];
const IL_ZOOM    = 6.4;

// Status palette (must match CSS vars)
const STATUS_COLORS = {
  available:  '#4f8a64',
  partial:    '#c79744',
  generating: '#6aa9ff',
  failed:     '#c8584d',
  missing:    '#2a313a',
};
const STATUS_HOVER = {
  available:  '#6ab885',
  partial:    '#d9b050',
  generating: '#84baff',
  failed:     '#de7065',
  missing:    '#3c4754',
};
const STATUS_LABELS = {
  available:  'Available',
  partial:    'Partial',
  generating: 'Generating',
  failed:     'Failed',
  missing:    'Missing',
};

// ── URL state ────────────────────────────────────────────────
// Hash format: #county=cook&z=9.5&lat=41.83&lng=-87.89
// All params optional. On load we restore; on change we push.

let _hashUpdateTimer = null;

function readHash() {
  const params = new URLSearchParams(window.location.hash.slice(1));
  return {
    county: params.get('county') || null,
    theme:  params.get('theme')  || null,
    z:      params.has('z')   ? parseFloat(params.get('z'))   : null,
    lat:    params.has('lat') ? parseFloat(params.get('lat')) : null,
    lng:    params.has('lng') ? parseFloat(params.get('lng')) : null,
  };
}

function writeHash(opts = {}) {
  const params = new URLSearchParams();
  const county = opts.county  ?? selectedId;
  const theme  = opts.theme   ?? activeTheme;
  const center = map ? map.getCenter() : null;
  const zoom   = map ? map.getZoom()   : null;
  if (county) params.set('county', county);
  if (theme)  params.set('theme',  theme);
  if (zoom   != null) params.set('z',   zoom.toFixed(2));
  if (center != null) { params.set('lat', center.lat.toFixed(5)); params.set('lng', center.lng.toFixed(5)); }
  const hash = '#' + params.toString();
  if (window.location.hash !== hash) {
    history.replaceState(null, '', hash);
  }
}

function scheduleHashUpdate() {
  clearTimeout(_hashUpdateTimer);
  _hashUpdateTimer = setTimeout(writeHash, 300);
}

// ── Runtime state ──────────────────────────────────────────────
let catalog    = null;
let statusIdx  = null;   // status/index.json
let map        = null;
let countyStatus = {};   // ilhmp_id → { status, tiles, jobs }

let hoveredId  = null;
let selectedId = null;   // ilhmp_id
let selectedFeatId = null;

let previewSourceId = null;
let previewLayerId  = null;
let activeTheme = null;  // for drawer preview

// ── Boot ───────────────────────────────────────────────────────
(async function boot() {
  // Register PMTiles protocol
  try {
    if (typeof pmtiles?.PMTilesProtocol === 'function') {
      const p = new pmtiles.PMTilesProtocol();
      maplibregl.addProtocol('pmtiles', p.tile);
    } else if (typeof pmtiles?.Protocol === 'function') {
      const p = new pmtiles.Protocol();
      maplibregl.addProtocol('pmtiles', p.tile);
    }
  } catch (e) {
    console.warn('[atlas] pmtiles protocol failed:', e);
  }

  // Load catalog
  try {
    const r = await fetch('catalog.json');
    catalog = await r.json();
  } catch (e) {
    console.error('[atlas] catalog load failed:', e);
    hideBoot();
    return;
  }

  // Load status index (non-fatal)
  try {
    const r = await fetch('/status/index.json');
    if (r.ok) statusIdx = await r.json();
  } catch (_) {}

  // Classify counties
  buildCountyStatus();

  // Render
  buildLegend();
  buildCoverage();
  buildMap();

  // Wire UI
  document.getElementById('drawer-close').addEventListener('click', closeDrawer);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeDrawer();
  });
})();

// ── Status classification ──────────────────────────────────────
function buildCountyStatus() {
  if (!catalog) return;

  // Build job index by county (most recent / worst status wins)
  const jobsByCounty = {};
  const STATUS_RANK = { running: 0, provisioning: 1, queued: 2, validating: 3, failed: 4, complete: 5 };
  for (const job of (statusIdx?.jobs || [])) {
    const cid = job.county;
    if (!cid) continue;
    const existing = jobsByCounty[cid];
    if (!existing || (STATUS_RANK[job.status] ?? 99) < (STATUS_RANK[existing.status] ?? 99)) {
      jobsByCounty[cid] = job;
    }
  }

  for (const [id, county] of Object.entries(catalog.counties)) {
    const tiles  = county.tiles || [];
    const job    = jobsByCounty[id] || null;
    const themes = catalog.themes || [];

    let status;
    const isGenerating = job && ['running', 'provisioning', 'queued', 'validating'].includes(job.status);
    const hasFailed    = job && job.status === 'failed' && tiles.length === 0;

    if (isGenerating) {
      status = 'generating';
    } else if (hasFailed) {
      status = 'failed';
    } else if (tiles.length === 0) {
      status = 'missing';
    } else if (themes.length > 0 && tiles.length < themes.length) {
      status = 'partial';
    } else {
      status = 'available';
    }

    countyStatus[id] = { status, tiles, job };
  }
}

// ── Map ─────────────────────────────────────────────────────────
function buildMap() {
  map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
      sources: {},
      layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#07090d' } }],
    },
    center: IL_CENTER,
    zoom: IL_ZOOM,
    minZoom: 4.5,
    maxZoom: 20,
    attributionControl: false,
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
  map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

  const zoomVal = document.getElementById('zoom-val');
  const updateZoom = () => { if (zoomVal) zoomVal.textContent = map.getZoom().toFixed(1); };
  map.on('zoom', updateZoom);
  map.on('moveend', scheduleHashUpdate);
  map.on('load', () => { updateZoom(); onMapLoad(); });
}

function onMapLoad() {
  // Build fill-color match expression from countyStatus
  map.addSource('counties', {
    type: 'geojson',
    data: 'counties.geojson',
    promoteId: 'ilhmp_id',
  });

  // Base fill — status choropleth
  map.addLayer({
    id: 'counties-fill',
    type: 'fill',
    source: 'counties',
    paint: {
      'fill-color': buildStatusExpression(),
      'fill-opacity': [
        'case',
        ['boolean', ['feature-state', 'selected'], false], 0.08,
        ['boolean', ['feature-state', 'hover'], false],    0.65,
        0.55,
      ],
    },
  });

  // Hover / selected highlight overlay
  map.addLayer({
    id: 'counties-highlight',
    type: 'fill',
    source: 'counties',
    paint: {
      'fill-color': buildStatusExpression(true),
      'fill-opacity': [
        'case',
        ['boolean', ['feature-state', 'selected'], false], 0.0,
        ['boolean', ['feature-state', 'hover'], false],    0.18,
        0.0,
      ],
    },
  });

  // Outline
  map.addLayer({
    id: 'counties-outline',
    type: 'line',
    source: 'counties',
    paint: {
      'line-color': [
        'case',
        ['boolean', ['feature-state', 'selected'], false], '#6aa9ff',
        'rgba(255,255,255,0.08)',
      ],
      'line-width': [
        'case',
        ['boolean', ['feature-state', 'selected'], false], 2.5,
        0.6,
      ],
    },
  });

  setupInteractions();

  // Restore state from URL hash
  const initial = readHash();
  if (initial.lat != null && initial.lng != null) {
    map.jumpTo({ center: [initial.lng, initial.lat], zoom: initial.z ?? IL_ZOOM });
  }
  if (initial.county && catalog.counties[initial.county]) {
    // Restore theme before selectCounty so it picks the right tile
    if (initial.theme) activeTheme = initial.theme;
    // Wait a tick so the map source is ready for feature-state
    requestAnimationFrame(() => selectCounty(initial.county));
  }

  hideBoot();
}

function buildStatusExpression(hover = false) {
  const args = [];
  for (const [id, info] of Object.entries(countyStatus)) {
    args.push(id, hover ? STATUS_HOVER[info.status] : STATUS_COLORS[info.status]);
  }
  args.push(STATUS_COLORS.missing); // fallback
  return ['match', ['get', 'ilhmp_id'], ...args];
}

// ── Interactions ───────────────────────────────────────────────
function setupInteractions() {
  const tip = document.getElementById('hover-tip');

  map.on('mousemove', 'counties-fill', (e) => {
    if (!e.features.length) return;
    const feat = e.features[0];
    const id   = feat.properties.ilhmp_id;
    if (!id) return;

    map.getCanvas().style.cursor = 'pointer';

    if (hoveredId && hoveredId !== id) {
      map.setFeatureState({ source: 'counties', id: hoveredId }, { hover: false });
    }
    hoveredId = id;
    map.setFeatureState({ source: 'counties', id }, { hover: true });

    // Tooltip
    const info   = countyStatus[id] || { status: 'missing' };
    const county = catalog.counties[id];
    const name   = county?.name || capitalize(id);
    const st     = info.status;
    const tile_count = info.tiles?.length || 0;

    const tipName = tip.querySelector('.name');
    const tipDot  = tip.querySelector('.status-dot');
    const tipText = tip.querySelector('.status-text');

    tipName.textContent  = name + ' County';
    tipDot.style.background = STATUS_COLORS[st];
    tipText.textContent  = STATUS_LABELS[st] + (st === 'available' && tile_count ? ` · ${tile_count} theme${tile_count !== 1 ? 's' : ''}` : '');

    tip.style.left = (e.originalEvent.clientX) + 'px';
    tip.style.top  = (e.originalEvent.clientY - 12) + 'px';
    tip.classList.add('show');
  });

  map.on('mouseleave', 'counties-fill', () => {
    map.getCanvas().style.cursor = '';
    if (hoveredId) {
      map.setFeatureState({ source: 'counties', id: hoveredId }, { hover: false });
      hoveredId = null;
    }
    tip.classList.remove('show');
  });

  map.on('click', 'counties-fill', (e) => {
    if (!e.features.length) return;
    const feat = e.features[0];
    const id   = feat.properties.ilhmp_id;
    if (!id) return;
    selectCounty(id);
  });

  // Click on empty = close
  map.on('click', (e) => {
    const hits = map.queryRenderedFeatures(e.point, { layers: ['counties-fill'] });
    if (!hits.length) closeDrawer();
  });
}

// ── Select + drawer ────────────────────────────────────────────
function selectCounty(id) {
  // Deselect previous
  if (selectedFeatId) {
    map.setFeatureState({ source: 'counties', id: selectedFeatId }, { selected: false });
  }
  selectedId = id;
  selectedFeatId = id;
  map.setFeatureState({ source: 'counties', id }, { selected: true });

  // Remove any existing preview
  removePreview();

  // Set default theme to first available
  const info = countyStatus[id] || {};
  activeTheme = info.tiles?.[0]?.theme || null;

  renderDrawer(id);
  openDrawer();
  writeHash();

  // Auto-load preview if available
  if (info.status === 'available' || info.status === 'partial') {
    const tile = getBestTile(id, activeTheme);
    if (tile) {
      setTimeout(() => showPreview(id, tile), 80);
    }
  }
}

function openDrawer() {
  const d = document.getElementById('drawer');
  d.classList.add('open');
  d.setAttribute('aria-hidden', 'false');
}

function closeDrawer() {
  const d = document.getElementById('drawer');
  d.classList.remove('open');
  d.setAttribute('aria-hidden', 'true');
  if (selectedFeatId) {
    map.setFeatureState({ source: 'counties', id: selectedFeatId }, { selected: false });
    selectedId = null;
    selectedFeatId = null;
  }
  removePreview();
  writeHash({ county: null });
}

// ── Drawer rendering ───────────────────────────────────────────
function renderDrawer(countyId) {
  const county = catalog.counties[countyId];
  if (!county) return;

  const info   = countyStatus[countyId] || { status: 'missing', tiles: [], job: null };
  const name   = county.name || capitalize(countyId);
  const dem    = county.sources?.dtm || county.sources?.dsm;
  const status = info.status;

  document.getElementById('drawer-title').textContent    = name + ' County';
  document.getElementById('drawer-subtitle').textContent = dem?.year ? `ILHMP LiDAR ${dem.year} · Illinois` : 'Illinois';

  const body = document.getElementById('drawer-body');

  // Status pill
  let html = `<div style="margin-bottom:14px;">${pillHTML(status)}</div>`;

  // Branch on status
  if (status === 'available' || status === 'partial') {
    html += renderAvailableBody(countyId, county, info, status);
  } else if (status === 'generating') {
    html += renderGeneratingBody(countyId, county, info);
  } else if (status === 'failed') {
    html += renderFailedBody(countyId, county, info);
  } else {
    html += renderMissingBody(countyId, county, info);
  }

  body.innerHTML = html;

  // Wire theme chips
  body.querySelectorAll('.theme-chip[data-theme]').forEach(chip => {
    chip.addEventListener('click', () => {
      const theme = chip.dataset.theme;
      activeTheme = theme;
      body.querySelectorAll('.theme-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      writeHash();
      const tile = getBestTile(countyId, theme);
      if (tile) showPreview(countyId, tile);
    });
  });

  // Wire action buttons
  const btnViewer = body.querySelector('#btn-open-viewer');
  if (btnViewer) {
    btnViewer.addEventListener('click', () => {
      const tile = getBestTile(countyId, activeTheme);
      if (!tile) return;
      window.open(`/configurator.html?county=${countyId}&theme=${tile.theme}`, '_blank');
    });
  }

  const btnRegen = body.querySelector('#btn-regenerate');
  if (btnRegen) {
    btnRegen.addEventListener('click', () => {
      window.open(buildGenerateUrl(countyId, county, 'simmon'), '_blank');
    });
  }

  const btnGenerate = body.querySelector('#btn-generate');
  if (btnGenerate) {
    btnGenerate.addEventListener('click', () => {
      window.open(buildGenerateUrl(countyId, county, 'simmon'), '_blank');
    });
  }

  const btnRetry = body.querySelector('#btn-retry');
  if (btnRetry) {
    btnRetry.addEventListener('click', () => {
      window.open(buildGenerateUrl(countyId, county, info.job?.theme || 'simmon'), '_blank');
    });
  }
}

function renderAvailableBody(countyId, county, info, status) {
  const tiles  = info.tiles || [];
  const themes = [...new Set(tiles.map(t => t.theme))];
  const allThemes = catalog.themes || [];
  const missingThemes = allThemes.filter(t => !themes.includes(t));
  const dem    = county.sources?.dtm;
  const bestTile = getBestTile(countyId, activeTheme);

  let html = '';

  // Theme picker
  html += `<div class="section-label">Available Themes</div>`;
  html += `<div class="theme-grid">`;
  for (const t of themes) {
    const isActive = t === (activeTheme || themes[0]);
    html += `<div class="theme-chip${isActive ? ' active' : ''}" data-theme="${t}">
      <span class="dot"></span>${themeLabel(t)}
    </div>`;
  }
  html += `</div>`;

  // Partial: show missing themes
  if (status === 'partial' && missingThemes.length) {
    html += `<div class="section-label" style="margin-top:14px;">Missing Themes</div>`;
    html += `<div class="theme-grid">`;
    for (const t of missingThemes) {
      html += `<div class="theme-chip" style="opacity:0.45;cursor:default;">${themeLabel(t)}</div>`;
    }
    html += `</div>`;
  }

  // Active tile meta
  if (bestTile) {
    const zoomLabel  = bestTile.zoom ? `z${bestTile.zoom[0]}–${bestTile.zoom[1]}` : '—';
    const exagLabel  = bestTile.exaggeration ? `${bestTile.exaggeration}×` : 'auto';
    const genDate    = bestTile.generated_at ? bestTile.generated_at.slice(0, 10) : '—';
    const sizeMB     = bestTile.pmtiles_size_mb || bestTile.mbtiles_size_mb;
    const sizeStr    = sizeMB ? (sizeMB >= 1024 ? (sizeMB/1024).toFixed(1)+' GB' : sizeMB+' MB') : '—';

    html += `<div class="section-label">Tile Details</div>
    <div class="meta-grid">
      <span class="k">Zoom</span><span class="v">${zoomLabel}</span>
      <span class="k">Exaggeration</span><span class="v">${exagLabel} vertical</span>
      <span class="k">Size</span><span class="v">${sizeStr}</span>
      <span class="k">Generated</span><span class="v">${genDate}</span>
      ${dem?.year ? `<span class="k">Source</span><span class="v">ISGS DTM ${dem.year}</span>` : ''}
    </div>`;
  }

  // Preview thumbnail placeholder (mini-map inlined as label)
  html += `<div class="section-label" style="margin-top:18px;">Preview</div>
  <div class="preview-thumb"><div class="ph">Loading tile…</div><div id="mini-map" class="mini-map"></div></div>`;

  // Actions
  const pmtilesUrl = bestTile ? `${TILES_BASE}/${bestTile.pmtiles}` : null;
  html += `<div class="action-row">
    <button class="btn btn-primary" id="btn-open-viewer">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 3C4.4 3 1.4 5.4.1 8c1.3 2.6 4.3 5 7.9 5s6.6-2.4 7.9-5C14.6 5.4 11.6 3 8 3zm0 8a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0-4.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/></svg>
      Open Viewer
    </button>
    ${pmtilesUrl ? `<a class="btn btn-secondary" href="${pmtilesUrl}" download>
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 12L3 7h3V2h4v5h3L8 12zm-7 2h14v2H1v-2z"/></svg>
      Download PMTiles
    </a>` : ''}
    <button class="btn btn-ghost" id="btn-regenerate">↺ Regenerate</button>
  </div>`;

  return html;
}

function renderGeneratingBody(countyId, county, info) {
  const job = info.job || {};
  const pct = Math.min(100, Math.max(0, job.percent || 0));
  const dem = county.sources?.dtm;
  const tiles = info.tiles || [];

  let html = '';

  if (tiles.length) {
    html += `<div class="section-label">Already Available</div>`;
    html += `<div class="theme-grid">`;
    for (const t of tiles) {
      html += `<div class="theme-chip"><span class="dot"></span>${themeLabel(t.theme)}</div>`;
    }
    html += `</div>`;
  }

  html += `<div class="section-label">Active Job</div>
  <div class="progress">
    <div class="label">
      <span>${job.theme ? themeLabel(job.theme) : 'Generating…'}</span>
      <span>${pct}%</span>
    </div>
    <div class="bar"><div style="width:${pct}%"></div></div>
    ${job.phase ? `<div class="phase">${job.phase.replace(/_/g, ' ')}</div>` : ''}
  </div>`;

  html += `<div class="meta-grid" style="margin-top:14px;">
    <span class="k">Status</span><span class="v">${STATUS_LABELS[job.status] || job.status || '—'}</span>
    ${job.updated_at ? `<span class="k">Updated</span><span class="v">${job.updated_at.slice(0,16).replace('T',' ')} UTC</span>` : ''}
    ${dem?.year ? `<span class="k">Source</span><span class="v">ISGS DTM ${dem.year}</span>` : ''}
  </div>`;

  html += `<div class="action-row">
    <a class="btn btn-secondary" href="/status.html" target="_blank">View Pipeline Status →</a>
  </div>`;

  return html;
}

function renderFailedBody(countyId, county, info) {
  const job = info.job || {};
  const dem = county.sources?.dtm;

  let html = '';

  html += `<div class="failure-msg">
    <div class="head">Generation failed</div>
    <div>${job.theme ? `Theme: ${themeLabel(job.theme)}` : 'Last run did not complete.'} ${job.phase ? `Failed at: ${job.phase.replace(/_/g, ' ')}` : ''}</div>
  </div>`;

  html += `<div class="meta-grid" style="margin-top:14px;">
    ${job.updated_at ? `<span class="k">Failed at</span><span class="v">${job.updated_at.slice(0,16).replace('T',' ')} UTC</span>` : ''}
    ${dem?.year ? `<span class="k">DEM year</span><span class="v">${dem.year}</span>` : ''}
    ${dem?.size_gb ? `<span class="k">DEM size</span><span class="v">${dem.size_gb} GB</span>` : ''}
  </div>`;

  html += `<div class="action-row">
    <button class="btn btn-generate" id="btn-retry">↺ Retry Generation</button>
    <a class="btn btn-ghost" href="/status.html" target="_blank">View Logs →</a>
  </div>`;

  return html;
}

function renderMissingBody(countyId, county, info) {
  const dem  = county.sources?.dtm || county.sources?.dsm;
  const sizeGb = dem?.size_gb;
  const estMin = sizeGb ? Math.round(sizeGb * 0.5) : null;
  const estCost = sizeGb ? (sizeGb * 0.001).toFixed(2) : null;

  let html = `
  <p class="missing-hint">This county has not yet been generated. LiDAR data is available — it just needs to be processed.</p>`;

  if (dem) {
    html += `<div class="meta-grid" style="margin-top:14px;">
      ${dem.year ? `<span class="k">DEM year</span><span class="v">${dem.year}</span>` : ''}
      ${sizeGb  ? `<span class="k">DEM size</span><span class="v">${sizeGb} GB raw</span>` : ''}
    </div>`;
  }

  if (estMin || estCost) {
    html += `<div class="est-row">
      ${estMin  ? `<div class="est"><strong>~${estMin} min</strong> to generate</div>` : ''}
      ${estCost ? `<div class="est"><strong>~$${estCost}</strong> EC2 cost</div>` : ''}
    </div>`;
  }

  html += `<div class="action-row" style="margin-top:20px;">
    <button class="btn btn-generate" id="btn-generate">
      <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm1 10H7V7h2v4zm0-5H7V4h2v2z"/></svg>
      Generate This County
    </button>
    <p class="missing-hint" style="text-align:center;margin-top:6px;font-size:11px;">Opens a PR in GitHub · estimated ~30 min</p>
  </div>`;

  return html;
}

// ── Preview (PMTiles raster overlay) ──────────────────────────
function showPreview(countyId, tile) {
  removePreview();
  if (!tile?.pmtiles) return;

  const srcId = 'preview-src';
  const layId = 'preview-layer';
  const url   = `pmtiles://${TILES_BASE}/${tile.pmtiles}`;

  map.addSource(srcId, { type: 'raster', url, tileSize: 256 });
  map.addLayer({ id: layId, type: 'raster', source: srcId,
    paint: { 'raster-opacity': 0.88 } }, 'counties-fill');

  previewSourceId = srcId;
  previewLayerId  = layId;

  // Fly to county
  const county = catalog.counties[countyId];
  if (county?.center) {
    map.flyTo({ center: county.center, zoom: Math.max(map.getZoom(), 9), duration: 900, essential: true });
  } else if (county?.bounds) {
    map.fitBounds([[county.bounds[0], county.bounds[1]], [county.bounds[2], county.bounds[3]]],
      { padding: 60, duration: 900 });
  }
}

function removePreview() {
  if (previewLayerId && map.getLayer(previewLayerId)) map.removeLayer(previewLayerId);
  if (previewSourceId && map.getSource(previewSourceId)) map.removeSource(previewSourceId);
  previewLayerId  = null;
  previewSourceId = null;
}

// ── Legend ─────────────────────────────────────────────────────
function buildLegend() {
  const counts = { available: 0, partial: 0, generating: 0, failed: 0, missing: 0 };
  for (const info of Object.values(countyStatus)) counts[info.status]++;

  const container = document.getElementById('legend-items');
  const order = ['available','partial','generating','failed','missing'];
  container.innerHTML = order.map(st => `
    <div class="legend-row">
      <div class="legend-swatch ${st}" style="background:${STATUS_COLORS[st]}"></div>
      ${STATUS_LABELS[st]}
      <span class="count">${counts[st]}</span>
    </div>`).join('');
}

// ── Coverage stats ─────────────────────────────────────────────
function buildCoverage() {
  const total   = Object.keys(countyStatus).length || 102;
  const covered = Object.values(countyStatus).filter(i => i.status === 'available' || i.status === 'partial').length;
  const gen     = Object.values(countyStatus).filter(i => i.status === 'generating').length;

  document.getElementById('cov-num').textContent = covered;

  const bar = document.getElementById('cov-bar');
  const covPct = Math.round((covered / total) * 100);
  const genPct = Math.round((gen / total) * 100);
  bar.innerHTML = `
    <div style="width:${covPct}%;background:${STATUS_COLORS.available};transition:width 0.6s"></div>
    <div style="width:${genPct}%;background:${STATUS_COLORS.generating};transition:width 0.6s"></div>`;
}

// ── Helpers ────────────────────────────────────────────────────
function getBestTile(countyId, theme) {
  const tiles = countyStatus[countyId]?.tiles || [];
  if (!tiles.length) return null;
  return tiles.find(t => t.theme === theme) || tiles[0];
}

function pillHTML(status) {
  return `<span class="status-pill ${status}">
    <span class="dot"></span>${STATUS_LABELS[status] || status}
  </span>`;
}

function themeLabel(id) {
  const map = {
    'simmon':          'Simmon',
    'simmon-light':    'Simmon Light',
    'atak-dark':       'ATAK Dark',
    'atak-light':      'ATAK Light',
    'tactical':        'Tactical',
    'flat-terrain':    'Flat Terrain',
    'grayscale':       'Grayscale',
    'vivid':           'Vivid',
    'vivid-elevation': 'Vivid Elev',
    'cool':            'Cool',
    'cool-elevation':  'Cool Elev',
  };
  return map[id] || id.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function buildGenerateUrl(countyId, county, theme) {
  const dem  = 'dtm';
  const exag = 'auto';
  const zoom = '10-16';
  const fn   = `${countyId}-${dem}-${theme}-${exag}x-z${zoom}.yaml`;
  const yaml = `county: ${countyId}\ndem: ${dem}\ntheme: ${theme}\nexaggeration: ${exag}\nzoom: "${zoom}"\nstatus: pending`;
  return `https://github.com/emuehlstein/illinois-hillshade-gen/new/main/requests?filename=${encodeURIComponent(fn)}&value=${encodeURIComponent(yaml)}`;
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
}

function hideBoot() {
  const el = document.getElementById('boot');
  el.classList.add('gone');
  setTimeout(() => el.remove(), 400);
}
