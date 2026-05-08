// ── Constants ──────────────────────────────────────────────────────────────
const TILES_BASE = 'https://exaggeratedrelief.s3.us-east-2.amazonaws.com';
const IL_CENTER  = [-89.3985, 40.6331];
const IL_ZOOM    = 6.2;
const GENERATE_URL_DEFAULT =
  'https://github.com/emuehlstein/illinois-hillshade-gen/edit/main/requests.yaml';

// ── State ──────────────────────────────────────────────────────────────────
let catalog       = null;
let selectorMap   = null;
let previewMap    = null;
let previewActive = false;
let previewLayerId = null;
let previewSourceId = null;

const state = {
  county: null,   // ilhmp_id string, e.g. "cook"
  dem:    'dtm',
  theme:  'atak-dark',
  exag:   '9',
  zoomMin: 10,
  zoomMax: 16,
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
    maxZoom: 12,
    attributionControl: false,
  });

  selectorMap.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left');
  selectorMap.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

  selectorMap.on('load', () => {
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

  // Update status card
  renderStatusCard();

  // Close any open preview when switching county
  closePreview();
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
  const matchArgs = [];
  for (const [id, county] of Object.entries(catalog.counties)) {
    const hasTile = findMatchingTile(id) !== null;
    matchArgs.push(id, hasTile ? '#1a4a2a' : '#1c2128');
  }
  // fallback
  matchArgs.push('#1c2128');

  return ['match', ['get', 'ilhmp_id'], ...matchArgs];
}

function refreshFillColors() {
  if (!selectorMap || !selectorMap.getLayer('counties-fill')) return;
  selectorMap.setPaintProperty('counties-fill', 'fill-color', buildAvailabilityExpression());
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
    const zoomMatch  =
      (t.zoom == null) ||
      (t.zoom[0] <= state.zoomMin && t.zoom[1] >= state.zoomMax) ||
      (t.zoom[0] === state.zoomMin && t.zoom[1] === state.zoomMax);
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

  if (tile) {
    const sizeMB   = tile.pmtiles_size_mb || tile.mbtiles_size_mb;
    const sizeStr  = sizeMB ? formatSize(sizeMB) : '—';
    const genDate  = tile.generated_at ? tile.generated_at.slice(0, 10) : '—';
    const demInfo  = countyData.sources?.[tile.dem];
    const sourceStr = demInfo ? `ISGS ILHMP ${tile.dem.toUpperCase()} ${demInfo.year || ''}` : tile.dem?.toUpperCase();
    const pmtilesUrl = `${TILES_BASE}/${tile.pmtiles}`;
    const exagLabel = tile.exaggeration ? `${tile.exaggeration}×` : 'auto';
    const zoomLabel = tile.zoom ? `z${tile.zoom[0]}–${tile.zoom[1]}` : '—';

    container.innerHTML = `
      <div class="status-header">
        <span class="status-badge available">✅ Available</span>
      </div>
      <div class="tile-meta">
        <div class="meta-row"><span class="meta-key">County</span><span class="meta-val">${countyName}</span></div>
        <div class="meta-row"><span class="meta-key">Theme</span><span class="meta-val">${tile.theme}</span></div>
        <div class="meta-row"><span class="meta-key">Exag</span><span class="meta-val">${exagLabel}</span></div>
        <div class="meta-row"><span class="meta-key">Zoom</span><span class="meta-val">${zoomLabel}</span></div>
        <div class="meta-row"><span class="meta-key">Size</span><span class="meta-val">${sizeStr}</span></div>
        <div class="meta-row"><span class="meta-key">Generated</span><span class="meta-val">${genDate}</span></div>
        <div class="meta-row"><span class="meta-key">Source</span><span class="meta-val">${sourceStr}</span></div>
      </div>
      <div class="action-row">
        <button class="btn btn-primary" id="btn-preview" onclick="openPreview()">👁 Preview</button>
        <a class="btn btn-secondary" href="${pmtilesUrl}" download>⬇ Download</a>
      </div>
    `;
  } else {
    // Not generated — show generate button
    const generateUrl = buildGenerateUrl(countyName);
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
      <div class="action-row">
        <a class="btn btn-green" href="${generateUrl}" target="_blank">🔧 Generate via PR</a>
      </div>
      <div class="generate-hint">
        Opens a GitHub PR to <code>requests.yaml</code>.<br/>
        Est. time: ~30 min · Est. cost: ~$0.07
      </div>
    `;
  }
}

function buildGenerateUrl(countyName) {
  const base = catalog.generate_url || GENERATE_URL_DEFAULT;
  const entry = [
    `  - county: ${state.county}`,
    `    dem: ${state.dem}`,
    `    theme: ${state.theme}`,
    `    exaggeration: ${state.exag}`,
    `    zoom: [${state.zoomMin}, ${state.zoomMax}]`,
  ].join('\n');
  // Open GitHub edit page; user can paste the entry
  return base + '#L1';
}

// ── Preview map ────────────────────────────────────────────────────────────
function openPreview() {
  const tile = findMatchingTile(state.county) || findBestTile(state.county);
  if (!tile) return;

  const section = document.getElementById('preview-section');
  const titleEl = document.getElementById('preview-title');
  const countyName = catalog.counties[state.county]?.name || capitalize(state.county);

  titleEl.textContent = `Preview — ${countyName} · ${tile.theme} · ${tile.exaggeration}× · z${tile.zoom?.[0]}–${tile.zoom?.[1]}`;

  const pmtilesUrl = `pmtiles://${TILES_BASE}/${tile.pmtiles}`;

  section.classList.remove('collapsed');
  section.classList.add('expanded');
  previewActive = true;

  if (!previewMap) {
    previewMap = new maplibregl.Map({
      container: 'preview-map',
      style: {
        version: 8,
        sources: {},
        layers: [{
          id: 'background',
          type: 'background',
          paint: { 'background-color': '#0d1117' },
        }],
      },
      center: getCountyCenter(),
      zoom: 9,
      attributionControl: false,
    });

    previewMap.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

    previewMap.on('load', () => {
      addPreviewLayer(tile, pmtilesUrl);
    });
  } else {
    // Map already exists — swap layer
    removePreviewLayer();
    if (previewMap.loaded()) {
      addPreviewLayer(tile, pmtilesUrl);
    } else {
      previewMap.once('idle', () => addPreviewLayer(tile, pmtilesUrl));
    }
    // Fly to county center
    const center = getCountyCenter();
    if (center) previewMap.flyTo({ center, zoom: 9, duration: 800 });
  }
}

function addPreviewLayer(tile, pmtilesUrl) {
  previewSourceId = `preview-${tile.id}`;
  previewLayerId  = `preview-layer-${tile.id}`;

  if (!previewMap.getSource(previewSourceId)) {
    previewMap.addSource(previewSourceId, {
      type: 'raster',
      url: pmtilesUrl,
      tileSize: 256,
    });
  }
  if (!previewMap.getLayer(previewLayerId)) {
    previewMap.addLayer({
      id: previewLayerId,
      type: 'raster',
      source: previewSourceId,
      paint: { 'raster-opacity': 1.0 },
    });
  }
}

function removePreviewLayer() {
  if (!previewMap) return;
  if (previewLayerId && previewMap.getLayer(previewLayerId)) {
    previewMap.removeLayer(previewLayerId);
  }
  if (previewSourceId && previewMap.getSource(previewSourceId)) {
    previewMap.removeSource(previewSourceId);
  }
  previewLayerId  = null;
  previewSourceId = null;
}

function closePreview() {
  const section = document.getElementById('preview-section');
  section.classList.remove('expanded');
  section.classList.add('collapsed');
  previewActive = false;
  removePreviewLayer();
}

document.getElementById('preview-close').addEventListener('click', closePreview);

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
  });

  // Theme dropdown
  document.getElementById('theme-select').addEventListener('change', (e) => {
    state.theme = e.target.value;
    renderStatusCard();
    refreshFillColors();
  });

  // Exaggeration radio group
  document.getElementById('exag-group').addEventListener('click', (e) => {
    const label = e.target.closest('label[data-val]');
    if (!label) return;
    state.exag = label.dataset.val;
    syncRadioGroup('exag-group', state.exag);
    renderStatusCard();
    refreshFillColors();
  });

  // Zoom inputs
  document.getElementById('zoom-min').addEventListener('change', (e) => {
    state.zoomMin = parseInt(e.target.value) || 10;
  });
  document.getElementById('zoom-max').addEventListener('change', (e) => {
    state.zoomMax = parseInt(e.target.value) || 16;
  });
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
