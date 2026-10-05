/**
 * Multi-Facility Operational Intelligence Dashboard Controller
 * Supports:
 * - Methode Electronics (Apodaca, MX)
 * - Aerostar Manufacturing (Romulus, MI)
 */

let appData = null;
let timeseriesChartInstance = null;
let shiftChartInstance = null;
let destinationChartInstance = null;

let currentPage = 1;
const rowsPerPage = 5;
let filteredManifests = [];
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
  document.getElementById("manifest-search").addEventListener("input", filterManifestTable);
  document.getElementById("destination-filter").addEventListener("change", filterManifestTable);
  document.getElementById("export-csv-btn").addEventListener("click", exportManifestCSV);

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
    console.error(`Failed to load pipeline data for ${facilityKey}:`, err);
    document.getElementById("status-text").innerText = "Data Sync Error";
  }
}

function renderDashboard(data) {
  if (!data) return;

  const kpis = data.kpis;
  const timeseries = data.timeseries || [];
  const manifests = data.manifests?.records || [];
  const sec = data.sec_telemetry || {};
  const meta = data.metadata?.facility_info || {};

  // Header & SEC Banner
  document.getElementById("header-facility-title").innerHTML = `${meta.facility || 'Operational Intelligence'}`;
  document.getElementById("header-facility-subtitle").innerText = `${meta.location || 'Industrial Movement Tracker'}`;

  document.getElementById("sec-company-name").innerText = `${sec.company_name || 'FACILITY TELEMETRY'} (${sec.ticker || 'REGISTRY'})`;
  if (sec.latest_inventory_usd) {
    document.getElementById("sec-inv-val").innerText = `$${(sec.latest_inventory_usd / 1000000).toFixed(1)}M`;
  }
  if (sec.latest_quarterly_revenue_usd) {
    document.getElementById("sec-rev-val").innerText = `$${(sec.latest_quarterly_revenue_usd / 1000000).toFixed(1)}M`;
  }

  // 1. Top KPI Cards
  document.getElementById("kpi-index-val").innerText = kpis.current_composite_index.toFixed(1);
  const badge = document.getElementById("kpi-status-badge");
  badge.innerText = kpis.status_label;
  badge.style.backgroundColor = `${kpis.status_color}25`;
  badge.style.color = kpis.status_color;

  const latestSub = timeseries[timeseries.length - 1]?.sub_scores || {};
  document.getElementById("sub-traffic").innerText = latestSub.traffic_congestion_score || '--';
  document.getElementById("sub-sat").innerText = latestSub.satellite_activity_score || '--';
  document.getElementById("sub-trade").innerText = latestSub.export_velocity_score || '--';

  document.getElementById("kpi-congestion-val").innerText = kpis.gate_congestion_pct.toFixed(1);
  document.getElementById("kpi-speed-val").innerText = kpis.gate_avg_speed_kmh.toFixed(1);
  document.getElementById("kpi-freeflow-val").innerText = kpis.gate_freeflow_speed_kmh.toFixed(1);
  document.getElementById("kpi-shift-delay").innerText = timeseries[timeseries.length - 1]?.traffic?.heavy_truck_dispatch_delay_mins || '12.5';

  document.getElementById("kpi-tonnage-val").innerText = kpis.trailing_30d_export_mt.toFixed(1);
  document.getElementById("kpi-teu-val").innerText = kpis.trailing_30d_teus;
  document.getElementById("kpi-top-port").innerText = currentFacilityKey === "aerostar" ? "Detroit Gateway" : "Laredo Land Port";

  document.getElementById("kpi-sat-date").innerText = kpis.latest_satellite_revisit_date;
  document.getElementById("kpi-cloud-val").innerText = kpis.latest_satellite_cloud_cover.toFixed(1);
  document.getElementById("kpi-utilization-val").innerText = kpis.latest_yard_utilization_pct.toFixed(1);

  // 2. Render Charts
  renderTimeseriesChart(timeseries);
  renderShiftProfileChart(timeseries);
  renderDestinationChart(data.manifests?.summary?.destinations || {});

  // 3. Render Manifest Table
  filteredManifests = [...manifests];
  filterManifestTable();
}

/* 6-Week Timeseries Chart */
function renderTimeseriesChart(timeseries) {
  const ctx = document.getElementById('timeseriesChart').getContext('2d');
  if (timeseriesChartInstance) timeseriesChartInstance.destroy();

  const labels = timeseries.map(t => t.date.slice(5));
  const indexData = timeseries.map(t => t.composite_index);
  const congestionData = timeseries.map(t => t.traffic.congestion_index);
  const satVarianceData = timeseries.map(t => t.satellite.yard_variance * 1000);

  timeseriesChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Composite Logistics Index (0-100)',
          data: indexData,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.12)',
          fill: true,
          tension: 0.3,
          borderWidth: 3,
          pointRadius: 3
        },
        {
          label: 'Gate Congestion Index (%)',
          data: congestionData,
          borderColor: '#f59e0b',
          borderDash: [5, 5],
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 2
        },
        {
          label: 'Staging Yard Variance (Scaled x1000)',
          data: satVarianceData,
          borderColor: '#10b981',
          borderDash: [2, 2],
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 12 } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 11 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 11 } }
        }
      }
    }
  });
}

/* Shift-Change Profile Chart */
function renderShiftProfileChart(timeseries) {
  const ctx = document.getElementById('shiftChart').getContext('2d');
  if (shiftChartInstance) shiftChartInstance.destroy();

  const shift6am = timeseries.map(t => t.traffic.shift_6am_congestion);
  const shift2pm = timeseries.map(t => t.traffic.shift_2pm_congestion);
  const shift10pm = timeseries.map(t => t.traffic.shift_10pm_congestion);

  const avg6 = (shift6am.reduce((a,b)=>a+b,0)/shift6am.length).toFixed(1);
  const avg2 = (shift2pm.reduce((a,b)=>a+b,0)/shift2pm.length).toFixed(1);
  const avg10 = (shift10pm.reduce((a,b)=>a+b,0)/shift10pm.length).toFixed(1);
  const avgOff = (avg6 * 0.4).toFixed(1);

  shiftChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Shift 1 (06:00 AM)', 'Shift 2 (02:00 PM)', 'Shift 3 (10:00 PM)', 'Inter-Shift Off-Peak'],
      datasets: [{
        label: 'Average Congestion Level (%)',
        data: [avg6, avg2, avg10, avgOff],
        backgroundColor: ['#ef4444', '#f59e0b', '#38bdf8', '#10b981'],
        borderRadius: 8,
        barThickness: 32
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 11 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: '#9ca3af', font: { family: 'Inter', size: 11 } }
        }
      }
    }
  });
}

/* Destination Tonnage Doughnut Chart */
function renderDestinationChart(destinations) {
  const ctx = document.getElementById('destinationChart').getContext('2d');
  if (destinationChartInstance) destinationChartInstance.destroy();

  const labels = Object.keys(destinations);
  const values = Object.values(destinations);

  destinationChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: ['#38bdf8', '#8b5cf6', '#10b981', '#f59e0b'],
        borderWidth: 2,
        borderColor: '#0b0f19'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#9ca3af', font: { family: 'Inter', size: 12 } }
        }
      },
      cutout: '65%'
    }
  });
}

/* Manifest Datatable Logic */
function filterManifestTable() {
  if (!appData || !appData.manifests) return;

  const searchTerm = document.getElementById("manifest-search").value.toLowerCase();
  const destFilter = document.getElementById("destination-filter").value;

  const allRecords = appData.manifests.records || [];

  filteredManifests = allRecords.filter(item => {
    const matchesSearch = 
      item.bol_id.toLowerCase().includes(searchTerm) ||
      item.shipper.toLowerCase().includes(searchTerm) ||
      item.consignee.toLowerCase().includes(searchTerm) ||
      item.hts_code.toLowerCase().includes(searchTerm) ||
      item.product_category.toLowerCase().includes(searchTerm);

    const matchesDest = (destFilter === "ALL") || (item.destination_port.includes(destFilter));

    return matchesSearch && matchesDest;
  });

  currentPage = 1;
  renderManifestTable();
}

function renderManifestTable() {
  const tbody = document.getElementById("manifest-tbody");
  tbody.innerHTML = "";

  const startIdx = (currentPage - 1) * rowsPerPage;
  const endIdx = startIdx + rowsPerPage;
  const pageItems = filteredManifests.slice(startIdx, endIdx);

  if (pageItems.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 24px;">No matching manifest records found.</td></tr>`;
  } else {
    pageItems.forEach(item => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family: var(--font-mono);">${item.date}</td>
        <td><span class="code-pill">${item.bol_id}</span></td>
        <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis;" title="${item.shipper}">${item.shipper}</td>
        <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis;" title="${item.consignee}">${item.consignee}</td>
        <td><span class="code-pill">${item.hts_code}</span></td>
        <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${item.product_category}">${item.product_category}</td>
        <td style="font-family: var(--font-mono); font-weight: 600; color: var(--accent-cyan);">${item.weight_mt} MT</td>
        <td style="font-family: var(--font-mono);">${item.teu_count}</td>
        <td><span style="font-size: 11px; background: rgba(56,189,248,0.12); color: #38bdf8; padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(56,189,248,0.3);">${item.sec_source || 'Registry'}</span></td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("table-showing-text").innerText = 
    `Showing ${filteredManifests.length > 0 ? startIdx + 1 : 0} to ${Math.min(endIdx, filteredManifests.length)} of ${filteredManifests.length} records`;

  renderPaginationControls();
}

function renderPaginationControls() {
  const container = document.getElementById("pagination-controls");
  container.innerHTML = "";

  const totalPages = Math.ceil(filteredManifests.length / rowsPerPage);
  if (totalPages <= 1) return;

  for (let i = 1; i <= totalPages; i++) {
    const btn = document.createElement("button");
    btn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
    btn.innerText = i;
    btn.addEventListener("click", () => {
      currentPage = i;
      renderManifestTable();
    });
    container.appendChild(btn);
  }
}

function exportManifestCSV() {
  if (!filteredManifests || filteredManifests.length === 0) return;

  const headers = ["Date", "BoL ID", "Shipper", "Consignee", "Origin Port", "Destination Port", "HTS Code", "Product Category", "Weight MT", "TEU Count", "Source Reference"];
  const rows = filteredManifests.map(b => [
    b.date, b.bol_id, `"${b.shipper}"`, `"${b.consignee}"`, `"${b.origin_port}"`, `"${b.destination_port}"`, b.hts_code, `"${b.product_category}"`, b.weight_mt, b.teu_count, `"${b.sec_source || 'Registry'}"`
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `${currentFacilityKey.toUpperCase()}_Manifests_Export_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
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
    console.log("Telemetry sync fallback executed.");
  } finally {
    btn.innerHTML = `<i class="fa-solid fa-rotate-right"></i> Refresh Telemetry`;
  }
}
