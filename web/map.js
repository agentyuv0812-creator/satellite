/**
 * Leaflet Interactive Map Module with Multi-Facility Support
 * Facilities:
 * 1. Methode Electronics (Apodaca, MX: [25.780, -100.130])
 * 2. Aerostar Manufacturing (Romulus, MI: [42.208, -83.393])
 */

let map;
let layersGroup;
let currentFacility = 'methode';

const FACILITY_MAP_CONFIGS = {
  methode: {
    title: "Apodaca Facility & Feeder Corridor Map",
    subtitle: "Coordinates: 25.780° N, -100.130° W | Bounding Box: [-100.138, 25.775, -100.122, 25.785]",
    center: [25.780, -100.130],
    bboxBounds: [[25.775, -100.138], [25.785, -100.122]],
    stagingCoords: [[25.782, -100.133], [25.782, -100.127], [25.778, -100.127], [25.778, -100.133]],
    dockCoords: [[25.781, -100.131], [25.781, -100.129], [25.779, -100.129], [25.779, -100.131]],
    feederRoads: [
      { name: "Carretera Miguel Alemán (Feeder)", coords: [[25.772, -100.145], [25.776, -100.138], [25.780, -100.130], [25.784, -100.125]], color: '#f59e0b', speed: '39.0 km/h', freeflow: '60.0 km/h' },
      { name: "Blvd. Agua Fría (Plant Gate Entrance)", coords: [[25.783, -100.135], [25.780, -100.130], [25.777, -100.128]], color: '#ef4444', speed: '18.2 km/h', freeflow: '50.0 km/h' },
      { name: "Av. Parque Industrial (Truck Dispatch Corridor)", coords: [[25.780, -100.130], [25.781, -100.122]], color: '#38bdf8', speed: '42.5 km/h', freeflow: '45.0 km/h' }
    ]
  },
  aerostar: {
    title: "Aerostar Manufacturing HQ & Corridor Map (Romulus, MI)",
    subtitle: "Coordinates: 42.208° N, -83.393° W | Bounding Box: [-83.401, 42.203, -83.385, 42.213]",
    center: [42.208, -83.393],
    bboxBounds: [[42.203, -83.401], [42.213, -83.385]],
    stagingCoords: [[42.210, -83.396], [42.210, -83.390], [42.206, -83.390], [42.206, -83.396]],
    dockCoords: [[42.209, -83.394], [42.209, -83.392], [42.207, -83.392], [42.207, -83.394]],
    feederRoads: [
      { name: "Northline Road (Plant Gate Access)", coords: [[42.208, -83.410], [42.208, -83.393], [42.208, -83.375]], color: '#38bdf8', speed: '45.0 mph', freeflow: '55.0 mph' },
      { name: "Inkster Road Corridor", coords: [[42.220, -83.393], [42.208, -83.393], [42.195, -83.393]], color: '#f59e0b', speed: '34.5 mph', freeflow: '45.0 mph' },
      { name: "I-94 Freight Expressway Connector", coords: [[42.215, -83.405], [42.210, -83.390]], color: '#10b981', speed: '62.0 mph', freeflow: '65.0 mph' }
    ]
  }
};

function initPlantMap() {
  if (!map) {
    map = L.map('plant-map', {
      zoomControl: true,
      scrollWheelZoom: false
    }).setView(FACILITY_MAP_CONFIGS.methode.center, 14);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      maxZoom: 16
    }).addTo(map);

    layersGroup = L.layerGroup().addTo(map);
  }

  updateMapForFacility('methode');

  document.getElementById('chip-all')?.addEventListener('click', (e) => {
    setActiveChip(e.target);
    const cfg = FACILITY_MAP_CONFIGS[currentFacility];
    map.fitBounds(cfg.bboxBounds, { padding: [30, 30] });
  });

  document.getElementById('chip-docks')?.addEventListener('click', (e) => {
    setActiveChip(e.target);
    const cfg = FACILITY_MAP_CONFIGS[currentFacility];
    map.setView(cfg.center, 16);
  });

  document.getElementById('chip-traffic')?.addEventListener('click', (e) => {
    setActiveChip(e.target);
    const cfg = FACILITY_MAP_CONFIGS[currentFacility];
    map.setView(cfg.center, 14);
  });
}

function updateMapForFacility(facilityKey) {
  const key = (facilityKey || 'methode').toLowerCase();
  currentFacility = key in FACILITY_MAP_CONFIGS ? key : 'methode';
  const cfg = FACILITY_MAP_CONFIGS[currentFacility];

  document.getElementById("map-title").innerText = cfg.title;
  document.getElementById("map-subtitle").innerText = cfg.subtitle;

  layersGroup.clearLayers();

  // 1. Facility Bounding Box
  const bboxRectangle = L.rectangle(cfg.bboxBounds, {
    color: '#38bdf8',
    weight: 2,
    dashArray: '6, 6',
    fillColor: '#38bdf8',
    fillOpacity: 0.08
  }).bindPopup(`
    <div style="font-family: sans-serif; padding: 4px;">
      <h4 style="margin: 0 0 6px 0; color: #38bdf8;">${currentFacility === 'aerostar' ? 'Aerostar Manufacturing' : 'Methode Electronics'} Target Node</h4>
      <p style="margin: 0; font-size: 12px; color: #333;">${cfg.subtitle}</p>
    </div>
  `);
  layersGroup.addLayer(bboxRectangle);

  // 2. Outdoor Trailer Holding Yard Polygon
  const stagingPolygon = L.polygon(cfg.stagingCoords, {
    color: '#10b981',
    weight: 2,
    fillColor: '#10b981',
    fillOpacity: 0.25
  }).bindPopup(`
    <div style="font-family: sans-serif; padding: 4px;">
      <h4 style="margin: 0 0 4px 0; color: #10b981;"><i class="fa-solid fa-trailer"></i> Outdoor Trailer Staging Yard</h4>
      <p style="margin: 0; font-size: 12px;"><strong>Facility:</strong> ${currentFacility.toUpperCase()}</p>
      <p style="margin: 2px 0 0 0; font-size: 12px;"><strong>Yard Occupancy:</strong> 78.5%</p>
    </div>
  `);
  layersGroup.addLayer(stagingPolygon);

  // 3. Loading Dock Zones Polygon
  const dockPolygon = L.polygon(cfg.dockCoords, {
    color: '#8b5cf6',
    weight: 2,
    fillColor: '#8b5cf6',
    fillOpacity: 0.4
  }).bindPopup(`
    <div style="font-family: sans-serif; padding: 4px;">
      <h4 style="margin: 0 0 4px 0; color: #8b5cf6;"><i class="fa-solid fa-boxes-packing"></i> Active Loading Docks</h4>
      <p style="margin: 0; font-size: 12px;">Operational Bay Turnover</p>
    </div>
  `);
  layersGroup.addLayer(dockPolygon);

  // 4. Feeder Roads
  cfg.feederRoads.forEach(road => {
    const line = L.polyline(road.coords, {
      color: road.color,
      weight: 5,
      opacity: 0.85
    }).bindPopup(`
      <div style="font-family: sans-serif; padding: 4px;">
        <h4 style="margin: 0 0 4px 0; color: ${road.color};">${road.name}</h4>
        <p style="margin: 0; font-size: 12px;"><strong>Current Speed:</strong> ${road.speed}</p>
        <p style="margin: 2px 0 0 0; font-size: 12px;"><strong>Free-flow Speed:</strong> ${road.freeflow}</p>
      </div>
    `);
    layersGroup.addLayer(line);
  });

  map.fitBounds(cfg.bboxBounds, { padding: [30, 30] });
}

function setActiveChip(activeBtn) {
  document.querySelectorAll('.map-chip').forEach(chip => chip.classList.remove('active'));
  activeBtn.classList.add('active');
}
