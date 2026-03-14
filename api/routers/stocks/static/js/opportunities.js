function fmtPct(x) {
  if (x === null || x === undefined || Number.isNaN(x)) return '-';
  return `${(x * 100).toFixed(2)}%`;
}

function fmtNum(x, digits = 2) {
  if (x === null || x === undefined || Number.isNaN(x)) return '-';
  return Number(x).toFixed(digits);
}

function fmtMoney(x) {
  if (x === null || x === undefined || Number.isNaN(x)) return '-';
  return `$${Number(x).toFixed(2)}`;
}

async function fetchJson(url) {
  const r = await fetch(url, { credentials: 'same-origin' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return await r.json();
}

function renderPlot(cands) {
  const xs = cands.map((c) => c.distToStrikePct ?? null);
  const ys = cands.map((c) => c.annYield ?? null);
  const sizes = cands.map((c) => Math.max(10, Math.min(40, (c.premium ?? 0) * 20)));
  const colors = cands.map((c) => c.score ?? 0);
  const text = cands.map((c) => `${c.ticker} ${c.expiry} (${c.dte}d)\nStrike ${c.strike} Premium ${c.premium}`);

  const trace = {
    x: xs,
    y: ys,
    mode: 'markers',
    type: 'scatter',
    text,
    hovertemplate: '%{text}<br>Ann Yield=%{y:.2f}<br>Dist=%{x:.2%}<extra></extra>',
    marker: {
      size: sizes,
      color: colors,
      colorscale: 'Viridis',
      showscale: true,
      opacity: 0.86,
      line: { width: 1, color: 'rgba(255,255,255,0.35)' }
    }
  };

  const layout = {
    margin: { l: 50, r: 20, t: 20, b: 50 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(255,255,255,0.85)',
    xaxis: { title: 'Distance to Strike', tickformat: ',.0%', gridcolor: 'rgba(11,18,32,0.08)' },
    yaxis: { title: 'Annualized Yield', tickformat: ',.2f', gridcolor: 'rgba(11,18,32,0.08)' }
  };

  Plotly.newPlot('plot', [trace], layout, { displayModeBar: false, responsive: true });
}

function upsertTable(dt, cands) {
  dt.clear();
  for (const c of cands) {
    dt.row.add([
      c.ticker,
      fmtNum(c.score, 1),
      fmtMoney(c.underlying),
      fmtMoney(c.strike),
      fmtMoney(c.premium),
      c.dte,
      c.expiry,
      fmtNum(c.annYield, 2),
      fmtPct(c.distToStrikePct),
      fmtPct(c.spreadPct)
    ]);
  }
  dt.draw();
}

$(document).ready(function () {
  const watchlistSelect = document.getElementById('watchlistSelect');
  const runBtn = document.getElementById('runBtn');
  const dteInput = document.getElementById('dteInput');
  const maxTickersInput = document.getElementById('maxTickersInput');
  const candCount = document.getElementById('candCount');
  const wlName = document.getElementById('wlName');

  const dt = $('#oppTable').DataTable({
    pageLength: 25,
    order: [[1, 'desc']],
    deferRender: true
  });

  async function loadWatchlists() {
    const wls = await fetchJson('/stocks/opportunities/watchlists');
    watchlistSelect.innerHTML = '';
    for (const wl of wls) {
      if (!wl.name) continue;
      const opt = document.createElement('option');
      opt.value = wl.name;
      opt.textContent = wl.name;
      watchlistSelect.appendChild(opt);
    }
    if (watchlistSelect.options.length) {
      wlName.textContent = watchlistSelect.value;
    }
  }

  async function runScan() {
    runBtn.disabled = true;
    runBtn.textContent = 'Running...';
    candCount.textContent = '-';
    wlName.textContent = watchlistSelect.value || '-';
    try {
      const wl = encodeURIComponent(watchlistSelect.value || '');
      const dte = encodeURIComponent(dteInput.value || '30');
      const maxT = encodeURIComponent(maxTickersInput.value || '40');
      const data = await fetchJson(`/stocks/opportunities.json?strategy=csp&watchlist=${wl}&target_dte=${dte}&max_tickers=${maxT}`);
      const cands = data.candidates || [];
      candCount.textContent = String(cands.length);
      renderPlot(cands);
      upsertTable(dt, cands);
    } catch (e) {
      console.error(e);
      alert(`Scan failed: ${e.message || e}`);
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = 'Run';
    }
  }

  runBtn.addEventListener('click', runScan);
  watchlistSelect.addEventListener('change', () => {
    wlName.textContent = watchlistSelect.value || '-';
  });

  loadWatchlists().catch((e) => {
    console.error(e);
    alert(`Failed to load watchlists: ${e.message || e}`);
  });
});

