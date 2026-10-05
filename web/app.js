/**
 * Multi-Facility Verified Telemetry Dashboard Controller
 * Displays provenanced STAC satellite passes, verified SEC EDGAR facts,
 * and explicit 'Not connected' states for unlinked components.
 */

let appData = null;
let currentFacilityKey = "methode";

document.addEventListener("DOMContentLoaded", () => {
  initPlantMap();
  
  const facilitySelect = document.getElementById("facility-select");
  facilitySelect.addEventListener("change", (e) => {
    currentFacilityKey = e.target.value;
    updateMapForFacility(currentFacilityKey);
    loadPipelineData(currentFacilityKey);
  });

  document.getElementById("refresh-btn").addEventListener("click", triggerTelemetryRefresh);
  loadPipelineData(currentFacilityKey);
});

async function loadPipelineData(facilityKey = "methode") {
  try {
    let response = await fetch(`/api/data?facility=${facilityKey}`);
    if (!response.ok) {
      const fallbackFile = facilityKey === "aerostar" ? "../data/pipeline_data_aerostar.json" : "../data/pipeline_data.json";
      response = await fetch(fallbackFile);
    }
    appData = await response.json();
    renderDashboard(appData);
  } catch (err) {
    console.error(`Failed to load telemetry for ${facilityKey}:`, err);
    document.getElementById("status-text").innerText = "Data Sync Error";
  }
}

function renderDashboard(data) {
  if (!data) return;

  const kpis = data.kpis || {};
  const scenes = data.satellite_scenes || [];
  const sec = data.sec_telemetry || {};
  const meta = data.metadata?.facility_info || {};
  const mode = data.metadata?.data_source_mode || {};

  // Header
  document.getElementById("header-facility-title").innerText = `${meta.facility || 'Facility Telemetry'}`;
  document.getElementById("header-facility-subtitle").innerText = `${meta.location || 'Verified STAC & Public Registry'}`;

  // SEC EDGAR Banner
  const secCompany = document.getElementById("sec-company-name");
  const secInv = document.getElementById("sec-inv-val");
  const secRev = document.getElementById("sec-rev-val");
  const secLink = document.getElementById("sec-link");

  if (currentFacilityKey === "aerostar") {
    secCompany.innerText = "Aerostar Manufacturing (Private Entity)";
    secInv.innerText = "No public SEC filings";
    secRev.innerText = "Private company";
    secLink.style.display = "none";
  } else {
    secCompany.innerText = `${sec.company_name || 'METHODE ELECTRONICS INC'} (CIK: 0000065270)`;
    secLink.style.display = "inline-flex";
    if (kpis.inventory && kpis.inventory.val) {
      secInv.innerText = `$${(kpis.inventory.val / 1000000).toFixed(1)}M (${kpis.inventory.period_end})`;
    } else {
      secInv.innerText = "No data";
    }
    if (kpis.revenue && kpis.revenue.val) {
      secRev.innerText = `$${(kpis.revenue.val / 1000000).toFixed(1)}M (${kpis.revenue.period_end})`;
    } else {
      secRev.innerText = "No data";
    }
  }

  // KPI 1: Composite Index (Disabled)
  document.getElementById("kpi-index-val").innerText = "--";
  document.getElementById("kpi-status-badge").innerText = "Disabled";
  document.getElementById("kpi-status-badge").style.backgroundColor = "rgba(107, 114, 128, 0.2)";
  document.getElementById("kpi-status-badge").style.color = "#9ca3af";

  // KPI 2: Traffic (Not Connected)
  if (kpis.gate_congestion_pct !== null && kpis.gate_congestion_pct !== undefined) {
    document.getElementById("kpi-congestion-val").innerText = `${kpis.gate_congestion_pct.toFixed(1)}%`;
    document.getElementById("kpi-traffic-reason").innerText = "Live TomTom Stream Active";
  } else {
    document.getElementById("kpi-congestion-val").innerText = "No data";
    document.getElementById("kpi-traffic-reason").innerText = kpis.traffic_reason || "No TOMTOM_API_KEY set in environment";
  }

  // KPI 3: Shipped Volume / Trade (Not Connected)
  document.getElementById("kpi-tonnage-val").innerText = "No data";

  // KPI 4: Satellite STAC Pass
  if (kpis.latest_satellite_revisit_date) {
    document.getElementById("kpi-sat-date").innerText = kpis.latest_satellite_revisit_date;
    document.getElementById("kpi-cloud-val").innerText = kpis.latest_satellite_cloud_cover !== null ? kpis.latest_satellite_cloud_cover.toFixed(1) : '--';
    const latestScene = scenes.length > 0 ? scenes[scenes.length - 1] : {};
    document.getElementById("kpi-nodata-val").innerText = latestScene.nodata_pixel_pct !== null && latestScene.nodata_pixel_pct !== undefined ? latestScene.nodata_pixel_pct.toFixed(1) : '--';
    
    if (kpis.latest_satellite_provenance) {
      const p = kpis.latest_satellite_provenance;
      document.getElementById("kpi-sat-source").innerHTML = `<i class="fa-solid fa-satellite"></i> Source: ${p.source} • Observed: ${p.observed_at}`;
    }
  } else {
    document.getElementById("kpi-sat-date").innerText = "No data";
    document.getElementById("kpi-cloud-val").innerText = "--";
    document.getElementById("kpi-nodata-val").innerText = "--";
  }

  // Render STAC Scenes Table
  renderSTACTable(scenes);

  // Render Provenance Summary Table
  renderProvenanceTable(data);
}

function renderSTACTable(scenes) {
  const tbody = document.getElementById("stac-tbody");
  tbody.innerHTML = "";

  if (!scenes || scenes.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 24px;">No satellite passes retrieved.</td></tr>`;
    return;
  }

  scenes.forEach(s => {
    const tr = document.createElement("tr");
    const cloudVal = s.cloud_cover_pct !== null ? `${s.cloud_cover_pct.toFixed(1)}%` : 'N/A';
    const nodataVal = s.nodata_pixel_pct !== null ? `${s.nodata_pixel_pct.toFixed(1)}%` : 'N/A';
    const b04Link = s.b04_url ? `<a href="${s.b04_url}" target="_blank" class="code-pill" style="color: #38bdf8;">View Signed B04 Asset</a>` : 'N/A';

    tr.innerHTML = `
      <td style="font-family: var(--font-mono); font-weight: 600;">${s.date}</td>
      <td><span class="code-pill">${s.scene_id}</span></td>
      <td>${cloudVal}</td>
      <td>${nodataVal}</td>
      <td>${b04Link}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderProvenanceTable(data) {
  const tbody = document.getElementById("provenance-tbody");
  tbody.innerHTML = "";

  const kpis = data.kpis || {};
  const meta = data.metadata || {};
  const mode = meta.data_source_mode || {};

  const provRows = [
    {
      component: "Satellite STAC Scenes",
      endpoint: "https://planetarycomputer.microsoft.com/api/stac/v1",
      status: mode.sentinel2_scenes === "live" ? "Connected (Live STAC)" : "Unavailable",
      statusColor: mode.sentinel2_scenes === "live" ? "#10b981" : "#ef4444",
      lastObserved: kpis.latest_satellite_revisit_date || "N/A",
      retrievedAt: kpis.latest_satellite_provenance?.retrieved_at || meta.last_updated || "N/A"
    },
    {
      component: "SEC EDGAR Inventory Facts",
      endpoint: "https://data.sec.gov/api/xbrl/companyfacts/CIK0000065270.json",
      status: kpis.inventory ? "Connected (Form 10-Q)" : "Not connected / Private entity",
      statusColor: kpis.inventory ? "#10b981" : "#f59e0b",
      lastObserved: kpis.inventory?.period_end || "N/A",
      retrievedAt: kpis.inventory?.provenance?.retrieved_at || meta.last_updated || "N/A"
    },
    {
      component: "SEC EDGAR Quarterly Revenue",
      endpoint: "https://data.sec.gov/api/xbrl/companyfacts/CIK0000065270.json",
      status: kpis.revenue ? "Connected (Form 10-Q)" : "Not connected / Private entity",
      statusColor: kpis.revenue ? "#10b981" : "#f59e0b",
      lastObserved: kpis.revenue?.period_end || "N/A",
      retrievedAt: kpis.revenue?.provenance?.retrieved_at || meta.last_updated || "N/A"
    },
    {
      component: "Gate Traffic Velocity",
      endpoint: "https://api.tomtom.com/traffic/services/4/flowSegmentData",
      status: kpis.gate_congestion_pct !== null ? "Connected (Live Stream)" : "Not connected (No TOMTOM_API_KEY)",
      statusColor: kpis.gate_congestion_pct !== null ? "#10b981" : "#f59e0b",
      lastObserved: kpis.gate_congestion_pct !== null ? meta.last_updated?.slice(0, 10) : "N/A",
      retrievedAt: meta.last_updated || "N/A"
    },
    {
      component: "Component Bills of Lading",
      endpoint: "US Customs & Trade Manifest API",
      status: "Not connected (Requires commercial provider license)",
      statusColor: "#f59e0b",
      lastObserved: "N/A",
      retrievedAt: meta.last_updated || "N/A"
    },
    {
      component: "Composite Activity Index",
      endpoint: "Internal Fused Pipeline Math",
      status: "Disabled (Awaiting minimum 2 connected live streams)",
      statusColor: "#6b7280",
      lastObserved: "N/A",
      retrievedAt: meta.last_updated || "N/A"
    }
  ];

  provRows.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-weight: 600;">${r.component}</td>
      <td style="font-family: var(--font-mono); font-size: 11px;">${r.endpoint}</td>
      <td><span style="background: ${r.statusColor}20; color: ${r.statusColor}; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">${r.status}</span></td>
      <td style="font-family: var(--font-mono);">${r.lastObserved}</td>
      <td style="font-family: var(--font-mono); font-size: 11px;">${r.retrievedAt}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function triggerTelemetryRefresh() {
  const btn = document.getElementById("refresh-btn");
  btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Updating...`;
  try {
    const res = await fetch('/api/trigger-update', { method: 'POST' });
    if (res.ok) {
      await loadPipelineData(currentFacilityKey);
    }
  } catch (err) {
    console.log("Telemetry refresh error.");
  } finally {
    btn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Refresh Telemetry`;
  }
}
