// ── Constants ──────────────────────────────────────────────────────────────
const TILES_BASE = 'https://exaggeratedrelief.s3.us-east-2.amazonaws.com';
const IL_CENTER  = [-89.3985, 40.6331];
const IL_ZOOM    = 6.2;
const GENERATE_URL_DEFAULT =
  'https://github.com/emuehlstein/illinois-hillshade-gen/edit/main/requests.yaml';

// ── State ──────────────────────────────────────────────────────────────────
let catalog       = null;
let statusIndex   = null;   // status/index.json (generation pipeline)
let selectorMap   = null;
let overlayActive = false;
let overlayLayerId = null;
let overlaySourceId = null;

const state = {
  county: null,   // ilhmp_id string, e.g. "cook"
  dem:    'dtm',
  theme:  'cool-elevation',
  exag:   '9',
  zooms: [10, 11, 12, 13, 14, 15, 16],
};

// ── Boot ───────────────────────────────────────────────────────────────────
(async function init() {
  console.log('[init] starting');
  // Register PMTiles protocol globally
  try {
    // PMTiles v4: addProtocol takes a callback, not a protocol object
    if (typeof pmtiles.PMTilesProtocol === 'function') {
      const protocol = new pmtiles.PMTilesProtocol();
      maplibregl.addProtocol('pmtiles', protocol.tile);
    } else if (typeof pmtiles.Protocol === 'function') {
      const protocol = new pmtiles.Protocol();
      maplibregl.addProtocol('pmtiles', protocol.tile);
    } else {
      console.warn('PMTiles protocol not available, tile preview disabled');
    }
  } catch (e) {
    console.error('[init] pmtiles protocol error:', e);
  }

  try {
    const resp = await fetch('catalog.json');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    catalog = await resp.json();
    console.log('[init] catalog loaded:', Object.keys(catalog.counties).length, 'counties');
  } catch (err) {
    showError('Failed to load catalog.json: ' + err.message);
    return;
  }

  // Load generation status index (non-fatal — best effort)
  try {
    const sresp = await fetch('/status/index.json');
    if (sresp.ok) {
      statusIndex = await sresp.json();
      console.log('[init] status index loaded:', (statusIndex.jobs || []).length, 'jobs');
    }
  } catch (e) {
    console.log('[init] status index unavailable (ok)');
  }

  try {
    populateCountyDropdown();
    console.log('[init] dropdown populated:', document.getElementById('county-select').options.length, 'options');
  } catch (e) {
    console.error('[init] populateCountyDropdown failed:', e);
  }

  try {
    buildSelectorMap();
    console.log('[init] map built');
  } catch (e) {
    console.error('[init] buildSelectorMap failed:', e);
  }

  try {
    updateStats();
    wireControls();
    console.log('[init] stats + controls wired');
  } catch (e) {
    console.error('[init] stats/controls failed:', e);
  }

  document.getElementById('loading-overlay').classList.add('hidden');
  console.log('[init] done');
})();

// ── County dropdown ────────────────────────────────────────────────────────
function populateCountyDropdown() {
  const sel = document.getElementById('county-select');
  const names = Object.entries(catalog.counties)
    .map(([id, c]) => ({ id, name: c.name || capitalize(id) }))
    .sort((a, b) => a.name.localeCompare(b.name));

  names.forEach(({ id, name }) => {
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = name;
    sel.appendChild(opt);
  });
}

// ── Selector map ───────────────────────────────────────────────────────────
function buildSelectorMap() {
  selectorMap = new maplibregl.Map({
    container: 'selector-map',
    style: {
      version: 8,
      sources: {},
      layers: [{
        id: 'background',
        type: 'background',
        paint: { 'background-color': '#0d1117' },
      }],
    },
    center: IL_CENTER,
    zoom: IL_ZOOM,
    minZoom: 5,
    maxZoom: 20,
    attributionControl: false,
  });

  selectorMap.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
  selectorMap.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

  selectorMap.on('zoom', () => {
    const z = selectorMap.getZoom();
    document.getElementById('stat-zoom').textContent = z.toFixed(1);
  });

  selectorMap.on('load', () => {
    document.getElementById('stat-zoom').textContent = selectorMap.getZoom().toFixed(1);
    selectorMap.addSource('counties', {
      type: 'geojson',
      data: 'counties.geojson',
    });

    // Base fill — color by availability
    selectorMap.addLayer({
      id: 'counties-fill',
      type: 'fill',
      source: 'counties',
      paint: {
        'fill-color': buildAvailabilityExpression(),
        'fill-opacity': 0.6,
      },
    });

    // Outline
    selectorMap.addLayer({
      id: 'counties-outline',
      type: 'line',
      source: 'counties',
      paint: {
        'line-color': '#30363d',
        'line-width': 0.7,
      },
    });

    // Hover highlight
    selectorMap.addLayer({
      id: 'counties-hover',
      type: 'fill',
      source: 'counties',
      paint: {
        'fill-color': '#58a6ff',
        'fill-opacity': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.25,
          0,
        ],
      },
    });

    // Selected fill
    selectorMap.addLayer({
      id: 'counties-selected',
      type: 'fill',
      source: 'counties',
      paint: {
        'fill-color': '#388bfd',
        'fill-opacity': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          0.35,
          0,
        ],
      },
    });

    // Selected outline
    selectorMap.addLayer({
      id: 'counties-selected-outline',
      type: 'line',
      source: 'counties',
      paint: {
        'line-color': '#58a6ff',
        'line-width': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          2,
          0,
        ],
      },
    });

    setupMapInteractions();
  });
}

let hoveredFeatureId = null;
let selectedFeatureId = null;

function setupMapInteractions() {
  selectorMap.on('mousemove', 'counties-fill', (e) => {
    selectorMap.getCanvas().style.cursor = 'pointer';
    if (e.features.length > 0) {
      if (hoveredFeatureId !== null) {
        selectorMap.setFeatureState({ source: 'counties', id: hoveredFeatureId }, { hover: false });
      }
      hoveredFeatureId = e.features[0].id;
      selectorMap.setFeatureState({ source: 'counties', id: hoveredFeatureId }, { hover: true });
    }
  });

  selectorMap.on('mouseleave', 'counties-fill', () => {
    selectorMap.getCanvas().style.cursor = '';
    if (hoveredFeatureId !== null) {
      selectorMap.setFeatureState({ source: 'counties', id: hoveredFeatureId }, { hover: false });
      hoveredFeatureId = null;
    }
  });

  selectorMap.on('click', 'counties-fill', (e) => {
    if (!e.features.length) return;
    const feat = e.features[0];
    const countyId = feat.properties.ilhmp_id;
    if (!countyId) return;
    selectCounty(countyId, feat.id);
  });
}

function selectCounty(countyId, featureId) {
  // Deselect previous
  if (selectedFeatureId !== null) {
    selectorMap.setFeatureState({ source: 'counties', id: selectedFeatureId }, { selected: false });
  }

  state.county = countyId;
  selectedFeatureId = featureId !== undefined ? featureId : getFeatureIdForCounty(countyId);

  if (selectedFeatureId !== null) {
    selectorMap.setFeatureState({ source: 'counties', id: selectedFeatureId }, { selected: true });
  }

  // Sync dropdown
  const sel = document.getElementById('county-select');
  sel.value = countyId;

  // Update status card + availability indicators
  renderStatusCard();
  updateAvailabilityDots();

  // Remove old overlay, then auto-show if a tile is available
  removeOverlay();
  // Auto-load the best available tile — no "Show on Map" click needed
  const autoTile = findMatchingTile(countyId) || findBestTile(countyId);
  if (autoTile) {
    // Slight delay so the status card renders first
    setTimeout(() => {
      showOverlay();
      const btn = document.getElementById('btn-preview');
      if (btn) { btn.textContent = '✕ Hide Map'; btn.classList.add('btn-active'); }
    }, 50);
  }
}

function getFeatureIdForCounty(countyId) {
  // Feature ids in the geojson are the FIPS strings like "17031"
  // We need to look it up from the catalog
  if (!catalog || !catalog.counties[countyId]) return null;
  const fips = catalog.counties[countyId].fips;
  if (!fips) return null;
  // GeoJSON feature id is the FIPS string (matches "id" property in geojson)
  return fips;
}

// ── Availability expression ────────────────────────────────────────────────
function buildAvailabilityExpression() {
  if (!catalog) return '#21262d';

  // Build a match expression: county ilhmp_id → color
  // Green = has ANY tiles, bright green = has tiles matching current config
  const matchArgs = [];
  for (const [id, county] of Object.entries(catalog.counties)) {
    const hasAny = county.tiles && county.tiles.length > 0;
    const hasMatch = findMatchingTile(id) !== null;
    matchArgs.push(id, hasMatch ? '#1a6a2a' : hasAny ? '#1a3a22' : '#1c2128');
  }
  // fallback
  matchArgs.push('#1c2128');

  return ['match', ['get', 'ilhmp_id'], ...matchArgs];
}

function refreshFillColors() {
  if (!selectorMap || !selectorMap.getLayer('counties-fill')) return;
  selectorMap.setPaintProperty('counties-fill', 'fill-color', buildAvailabilityExpression());
}

function updateAvailabilityDots() {
  if (!state.county || !catalog) return;
  const county = catalog.counties[state.county];
  if (!county) return;
  const tiles = county.tiles || [];

  // Check each theme option against available tiles
  document.querySelectorAll('#theme-group label[data-val]').forEach(label => {
    const theme = label.dataset.val;
    const has = tiles.some(t => t.theme === theme && t.dem === state.dem);
    const dot = label.querySelector('.avail-dot');
    if (dot) { dot.className = 'avail-dot ' + (has ? 'has-tile' : 'no-tile'); }
  });

  // Check each DEM option
  document.querySelectorAll('#dem-group label[data-val]').forEach(label => {
    const dem = label.dataset.val;
    const has = tiles.some(t => t.dem === dem && t.theme === state.theme);
    const dot = label.querySelector('.avail-dot');
    if (dot) { dot.className = 'avail-dot ' + (has ? 'has-tile' : 'no-tile'); }
  });

  // Check each exaggeration option
  document.querySelectorAll('#exag-group label[data-val]').forEach(label => {
    const exag = label.dataset.val;
    const has = tiles.some(t =>
      t.dem === state.dem &&
      t.theme === state.theme &&
      (exag === 'auto' || String(t.exaggeration) === exag)
    );
    const dot = label.querySelector('.avail-dot');
    if (dot) { dot.className = 'avail-dot ' + (has ? 'has-tile' : 'no-tile'); }
  });
}

// ── Tile matching ──────────────────────────────────────────────────────────
function findMatchingTile(countyId) {
  if (!catalog) return null;
  const county = catalog.counties[countyId];
  if (!county || !county.tiles || !county.tiles.length) return null;

  return county.tiles.find(t => {
    const themeMatch = t.theme === state.theme;
    const demMatch   = t.dem   === state.dem;
    const exagMatch  = String(t.exaggeration) === String(state.exag) || state.exag === 'auto';
    return themeMatch && demMatch && exagMatch;
  }) || null;
}

function findBestTile(countyId) {
  // Fallback: any tile for this county with matching dem
  if (!catalog) return null;
  const county = catalog.counties[countyId];
  if (!county || !county.tiles || !county.tiles.length) return null;
  return (
    county.tiles.find(t => t.dem === state.dem) ||
    county.tiles[0] ||
    null
  );
}

// ── Status card ────────────────────────────────────────────────────────────
function renderStatusCard() {
  const container = document.getElementById('status-content');
  if (!state.county) {
    container.innerHTML = `<div style="color: #6e7681; font-size: 12px;">Select a county to see availability.</div>`;
    return;
  }

  const countyData = catalog.counties[state.county];
  if (!countyData) {
    container.innerHTML = `<div style="color: #f85149; font-size: 12px;">County not found in catalog.</div>`;
    return;
  }

  const tile = findMatchingTile(state.county);
  const countyName = countyData.name || capitalize(state.county);

  // Look up any active/recent pipeline job for this county+theme combo
  const activeJob = findActiveJob(state.county, state.theme);
  const jobStatusHtml = activeJob ? renderInlineJobStatus(activeJob) : '';

  if (tile) {
    const sizeMB   = tile.pmtiles_size_mb || tile.mbtiles_size_mb;
    const sizeStr  = sizeMB ? formatSize(sizeMB) : '—';
    const genDate  = tile.generated_at ? tile.generated_at.slice(0, 10) : '—';
    const demInfo  = countyData.sources?.[tile.dem];
    const sourceStr = demInfo ? `ISGS ILHMP ${tile.dem.toUpperCase()} ${demInfo.year || ''}` : tile.dem?.toUpperCase();
    const pmtilesUrl = `${TILES_BASE}/${tile.pmtiles}`;
    const exagLabel = tile.exaggeration ? `${tile.exaggeration}×` : 'auto';
    const zoomLabel = tile.zoom ? `z${tile.zoom[0]}–${tile.zoom[1]}` : '—';
    const selectedZoomLabel = formatZoomList(state.zooms);

    container.innerHTML = `
      <div class="status-header">
        <span class="status-badge available">✅ Available</span>
      </div>
      <div class="tile-meta">
        <div class="meta-row"><span class="meta-key">County</span><span class="meta-val">${countyName}</span></div>
        <div class="meta-row"><span class="meta-key">Theme</span><span class="meta-val">${tile.theme}</span></div>
        <div class="meta-row"><span class="meta-key">Exag</span><span class="meta-val">${exagLabel}</span></div>
        <div class="meta-row"><span class="meta-key">Tile zoom</span><span class="meta-val">${zoomLabel}</span></div>
        <div class="meta-row"><span class="meta-key">Selected</span><span class="meta-val">${selectedZoomLabel}</span></div>
        <div class="meta-row"><span class="meta-key">Size</span><span class="meta-val">${sizeStr}</span></div>
        <div class="meta-row"><span class="meta-key">Generated</span><span class="meta-val">${genDate}</span></div>
        <div class="meta-row"><span class="meta-key">Source</span><span class="meta-val">${sourceStr}</span></div>
      </div>
      ${jobStatusHtml}
      <div class="action-row">
        <button class="btn btn-primary" id="btn-preview" onclick="toggleOverlay()">👁 Show on Map</button>
        <a class="btn btn-secondary" href="${pmtilesUrl}" download>⬇ Download</a>
      </div>
    `;
  } else {
    // Not generated — show generate button
    const { url: generateUrl, filename } = buildGenerateUrl(countyName);
    const demSrc = countyData.sources?.[state.dem];
    const demYear = demSrc?.year || '?';
    const demSize = demSrc?.size_gb ? `${demSrc.size_gb} GB DEM` : '';

    container.innerHTML = `
      <div class="status-header">
        <span class="status-badge missing">⏳ Not yet generated</span>
      </div>
      <div class="tile-meta">
        <div class="meta-row"><span class="meta-key">County</span><span class="meta-val">${countyName}</span></div>
        <div class="meta-row"><span class="meta-key">DEM year</span><span class="meta-val">${demYear}</span></div>
        ${demSize ? `<div class="meta-row"><span class="meta-key">DEM size</span><span class="meta-val">${demSize}</span></div>` : ''}
      </div>
      ${jobStatusHtml}
      <div class="action-row">
        <a class="btn btn-green" href="${generateUrl}" target="_blank">🔧 Generate via PR</a>
      </div>
      <div class="generate-hint">
        Creates <code>requests/${filename}</code> and opens a PR.<br/>
        Each request is a separate file — no merge conflicts.<br/>
        Est. time: ~30 min · Est. cost: ~$0.07
      </div>
    `;
  }
}

// ── Inline pipeline status helpers ────────────────────────────────────────────

function findActiveJob(countyId, theme) {
  if (!statusIndex || !statusIndex.jobs) return null;
  // Match county; theme matching is fuzzy (prefix) since theme keys vary
  return statusIndex.jobs.find(j =>
    j.county === countyId &&
    (j.theme === theme || j.theme?.startsWith(theme) || theme?.startsWith(j.theme))
  ) || statusIndex.jobs.find(j => j.county === countyId) || null;
}

function renderInlineJobStatus(job) {
  const status = job.status || 'unknown';
  const phase = job.phase || '';
  const pct = Math.max(0, Math.min(100, job.percent || 0));

  const BADGE_COLORS = {
    complete:     'color:#3fb950;background:#1a4731;border-color:#238636',
    running:      'color:#58a6ff;background:#0c2d6b;border-color:#1f6feb',
    uploading:    'color:#79c0ff;background:#0c2d6b;border-color:#1f6feb',
    queued:       'color:#d29922;background:#2d1b00;border-color:#9e6a03',
    validating:   'color:#d29922;background:#2d1b00;border-color:#9e6a03',
    provisioning: 'color:#d29922;background:#2d1b00;border-color:#9e6a03',
    failed:       'color:#f85149;background:#3d1212;border-color:#8e1519',
    cancelled:    'color:#6e7681;background:#21262d;border-color:#30363d',
  };
  const badgeStyle = BADGE_COLORS[status] || BADGE_COLORS.cancelled;

  // Only show bar when actively in-progress
  const showBar = ['running','uploading','provisioning','queued','validating'].includes(status);
  const barHtml = showBar ? `
    <div style="height:3px;background:#21262d;border-radius:2px;margin-top:6px;overflow:hidden;">
      <div style="height:100%;width:${pct}%;background:#388bfd;border-radius:2px;"></div>
    </div>` : '';

  return `
    <div style="margin:8px 0;padding:8px 10px;background:#0d1117;border:1px solid #30363d;border-radius:6px;">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;">
        <span style="font-size:11px;color:#8b949e;">Pipeline</span>
        <span style="display:inline-block;font-size:10px;font-weight:600;padding:1px 7px;border-radius:10px;border:1px solid;${badgeStyle};text-transform:uppercase;">${status}</span>
      </div>
      <div style="font-size:11px;color:#8b949e;margin-top:3px;font-family:monospace;">${phase}${pct ? ' · ' + pct + '%' : ''}</div>
      ${barHtml}
      <div style="margin-top:6px;font-size:11px;">
        <a href="/status.html" style="color:#58a6ff;text-decoration:none;">→ View on status page</a>
      </div>
    </div>
  `;
}

function buildGenerateUrl(countyName) {
  // Build a unique filename from the config
  const zoomStr = formatZoomCompact(state.zooms);
  const filename = `${state.county}-${state.dem}-${state.theme}-${state.exag}x-z${zoomStr}.yaml`;

  const yaml = [
    `county: ${state.county}`,
    `dem: ${state.dem}`,
    `theme: ${state.theme}`,
    `exaggeration: ${state.exag}`,
    `zoom: "${formatZoomCompact(state.zooms)}"`,
    `status: pending`,
  ].join('\n');

  // GitHub new-file URL: creates requests/<filename> with pre-filled content
  const url = `https://github.com/emuehlstein/illinois-hillshade-gen/new/main/requests?filename=${encodeURIComponent(filename)}&value=${encodeURIComponent(yaml)}`;
  return { url, filename };
}

// ── Preview map ────────────────────────────────────────────────────────────
function toggleOverlay() {
  if (overlayActive) {
    removeOverlay();
    const btn = document.getElementById('btn-preview');
    if (btn) { btn.textContent = '👁 Show on Map'; btn.classList.remove('btn-active'); }
  } else {
    showOverlay();
    const btn = document.getElementById('btn-preview');
    if (btn) { btn.textContent = '✕ Hide Map'; btn.classList.add('btn-active'); }
  }
}

const COUNTY_FILL_LAYERS = ['counties-fill', 'counties-hover', 'counties-selected', 'counties-selected-outline'];

function removeOverlay() {
  if (!selectorMap) return;
  if (overlayLayerId && selectorMap.getLayer(overlayLayerId)) {
    selectorMap.removeLayer(overlayLayerId);
  }
  if (overlaySourceId && selectorMap.getSource(overlaySourceId)) {
    selectorMap.removeSource(overlaySourceId);
  }
  overlayLayerId  = null;
  overlaySourceId = null;
  overlayActive = false;
  // Restore county fill layers
  COUNTY_FILL_LAYERS.forEach(id => {
    if (selectorMap.getLayer(id)) {
      selectorMap.setLayoutProperty(id, 'visibility', 'visible');
    }
  });
}

function showOverlay() {
  const tile = findMatchingTile(state.county) || findBestTile(state.county);
  if (!tile || !selectorMap) return;

  removeOverlay();

  const pmtilesUrl = `pmtiles://${TILES_BASE}/${tile.pmtiles}`;
  overlaySourceId = `overlay-${tile.id}`;
  overlayLayerId  = `overlay-layer-${tile.id}`;

  if (!selectorMap.getSource(overlaySourceId)) {
    selectorMap.addSource(overlaySourceId, {
      type: 'raster',
      url: pmtilesUrl,
      tileSize: 256,
    });
  }
  if (!selectorMap.getLayer(overlayLayerId)) {
    // Insert below county outlines so borders stay visible
    const beforeLayer = selectorMap.getLayer('counties-outline') ? 'counties-outline' : undefined;
    selectorMap.addLayer({
      id: overlayLayerId,
      type: 'raster',
      source: overlaySourceId,
      paint: { 'raster-opacity': 0.9 },
    }, beforeLayer);
  }

  overlayActive = true;

  // Hide county fill layers so they don't obscure the hillshade
  COUNTY_FILL_LAYERS.forEach(id => {
    if (selectorMap.getLayer(id)) {
      selectorMap.setLayoutProperty(id, 'visibility', 'none');
    }
  });

  // Fly to the county
  const center = getCountyCenter();
  const zoom = Math.max(Math.min(...state.zooms) || 10, selectorMap.getZoom());
  if (center) selectorMap.flyTo({ center, zoom, duration: 800 });
}



function getCountyCenter() {
  if (!state.county || !catalog) return IL_CENTER;
  const c = catalog.counties[state.county];
  if (c?.center) return c.center;
  if (c?.bounds) {
    return [
      (c.bounds[0] + c.bounds[2]) / 2,
      (c.bounds[1] + c.bounds[3]) / 2,
    ];
  }
  return IL_CENTER;
}

// ── Stats bar ──────────────────────────────────────────────────────────────
function updateStats() {
  if (!catalog) return;
  const counties = Object.keys(catalog.counties).length;
  let tiles = 0;
  let totalMB = 0;
  for (const county of Object.values(catalog.counties)) {
    tiles += (county.tiles || []).length;
    for (const t of (county.tiles || [])) {
      totalMB += t.pmtiles_size_mb || t.mbtiles_size_mb || 0;
    }
  }
  document.getElementById('stat-counties').textContent = counties;
  document.getElementById('stat-tiles').textContent = tiles;
  document.getElementById('stat-size').textContent = totalMB ? formatSize(totalMB) : '—';
}

// ── Wire up controls ───────────────────────────────────────────────────────
function wireControls() {
  // County dropdown
  document.getElementById('county-select').addEventListener('change', (e) => {
    if (!e.target.value) return;
    const countyId = e.target.value;
    selectCounty(countyId);
  });

  // DEM radio group
  document.getElementById('dem-group').addEventListener('click', (e) => {
    const label = e.target.closest('label[data-val]');
    if (!label) return;
    state.dem = label.dataset.val;
    syncRadioGroup('dem-group', state.dem);
    renderStatusCard();
    refreshFillColors();
    updateAvailabilityDots();
  });

  // Theme button group
  document.getElementById('theme-group').addEventListener('click', (e) => {
    const label = e.target.closest('label[data-val]');
    if (!label) return;
    state.theme = label.dataset.val;
    syncRadioGroup('theme-group', state.theme);
    renderStatusCard();
    refreshFillColors();
    updateAvailabilityDots();
  });

  // Exaggeration radio group
  document.getElementById('exag-group').addEventListener('click', (e) => {
    const label = e.target.closest('label[data-val]');
    if (!label) return;
    state.exag = label.dataset.val;
    syncRadioGroup('exag-group', state.exag);
    renderStatusCard();
    refreshFillColors();
    updateAvailabilityDots();
  });

  // Zoom chips
  buildZoomChips();

  // Sync all radio groups to initial state (so UI matches state defaults)
  syncRadioGroup('dem-group', state.dem);
  syncRadioGroup('theme-group', state.theme);
  syncRadioGroup('exag-group', state.exag);
}

function syncRadioGroup(groupId, activeVal) {
  const group = document.getElementById(groupId);
  group.querySelectorAll('label[data-val]').forEach(label => {
    label.classList.toggle('active', label.dataset.val === activeVal);
  });
}

// ── Helpers ────────────────────────────────────────────────────────────────
function formatSize(mb) {
  if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB';
  return mb + ' MB';
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Zoom chip controls ──────────────────────────────────────────────
const ZOOM_MIN = 0;
const ZOOM_MAX = 22;

function buildZoomChips() {
  const container = document.getElementById('zoom-chips');
  if (!container) return;
  container.innerHTML = '';
  for (let z = ZOOM_MIN; z <= ZOOM_MAX; z++) {
    const chip = document.createElement('div');
    chip.className = 'zoom-chip' + (state.zooms.includes(z) ? ' active' : '');
    chip.textContent = z;
    chip.dataset.zoom = z;
    chip.addEventListener('click', () => toggleZoom(z));
    container.appendChild(chip);
  }
}

function toggleZoom(z) {
  const idx = state.zooms.indexOf(z);
  if (idx >= 0) {
    state.zooms.splice(idx, 1);
  } else {
    state.zooms.push(z);
    state.zooms.sort((a, b) => a - b);
  }
  syncZoomChips();
}

function syncZoomChips() {
  document.querySelectorAll('.zoom-chip').forEach(chip => {
    const z = parseInt(chip.dataset.zoom);
    chip.classList.toggle('active', state.zooms.includes(z));
  });
}

function zoomSelectRange(lo, hi) {
  state.zooms = [];
  for (let z = lo; z <= hi; z++) state.zooms.push(z);
  syncZoomChips();
}

function zoomSelectAll() {
  state.zooms = [];
  for (let z = ZOOM_MIN; z <= ZOOM_MAX; z++) state.zooms.push(z);
  syncZoomChips();
}

function zoomSelectNone() {
  state.zooms = [];
  syncZoomChips();
}

function formatZoomList(zooms) {
  if (!zooms || zooms.length === 0) return '—';
  const sorted = [...zooms].sort((a, b) => a - b);
  // Group into contiguous runs
  const runs = [];
  let start = sorted[0], prev = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === prev + 1) {
      prev = sorted[i];
    } else {
      runs.push(start === prev ? `z${start}` : `z${start}–${prev}`);
      start = sorted[i];
      prev = sorted[i];
    }
  }
  runs.push(start === prev ? `z${start}` : `z${start}–${prev}`);
  return runs.join(', ');
}

function formatZoomCompact(zooms) {
  if (!zooms || zooms.length === 0) return '0';
  const sorted = [...zooms].sort((a, b) => a - b);
  const runs = [];
  let start = sorted[0], prev = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === prev + 1) {
      prev = sorted[i];
    } else {
      runs.push(start === prev ? `${start}` : `${start}-${prev}`);
      start = sorted[i];
      prev = sorted[i];
    }
  }
  runs.push(start === prev ? `${start}` : `${start}-${prev}`);
  return runs.join(',');
}

// ── Mobile bottom sheet toggle ─────────────────────────────────────────────
(function initMobileSheet() {
  const panel = document.getElementById('config-panel');
  const handle = document.getElementById('config-handle');
  if (!panel || !handle) return;

  const label = handle.querySelector('.handle-label');

  handle.addEventListener('click', () => {
    const expanded = panel.classList.toggle('expanded');
    if (label) label.textContent = expanded ? 'Controls ▼' : 'Controls ▲';
  });

  // Collapse when clicking the map on mobile
  const mapEl = document.getElementById('selector-map');
  if (mapEl) {
    mapEl.addEventListener('click', () => {
      if (window.innerWidth <= 640 && panel.classList.contains('expanded')) {
        panel.classList.remove('expanded');
        if (label) label.textContent = 'Controls ▲';
      }
    });
  }
})();

function showError(msg) {
  const overlay = document.getElementById('loading-overlay');
  overlay.innerHTML = `
    <div style="color: #f85149; font-size: 14px; text-align: center; max-width: 400px; padding: 20px;">
      <div style="font-size: 24px; margin-bottom: 12px;">⚠️</div>
      <strong>Error</strong><br/>
      <span style="color: #8b949e; font-size: 12px;">${msg}</span>
    </div>
  `;
}
