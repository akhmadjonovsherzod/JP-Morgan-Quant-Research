const RISK_COLORS = {
  1: '#1e8e5a', 2: '#7cb518', 3: '#e3a008',
  4: '#e8730a', 5: '#d8412f', 6: '#6d3f91',
};

let ratingChart = null;
let ficoChart = null;

// ---------------------------------------------------------------- helpers

async function getJSON(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function money(n) {
  if (n === null || n === undefined) return '—';
  return '$' + Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function pct(n) {
  if (n === null || n === undefined) return '—';
  return (Number(n) * 100).toFixed(1) + '%';
}

// ---------------------------------------------------------------- health

async function loadHealth() {
  const el = document.getElementById('db-status');
  try {
    const health = await getJSON('/api/health');
    if (health.database_connected) {
      el.textContent = 'database connected';
      el.className = 'db-status ok';
    } else {
      el.textContent = 'database unreachable';
      el.className = 'db-status down';
    }
  } catch {
    el.textContent = 'API unreachable';
    el.className = 'db-status down';
  }
}

// ---------------------------------------------------------------- scoring form

function readForm() {
  return {
    customer_id: Number(document.getElementById('customer_id').value),
    credit_lines_outstanding: Number(document.getElementById('credit_lines_outstanding').value),
    loan_amt_outstanding: Number(document.getElementById('loan_amt_outstanding').value),
    total_debt_outstanding: Number(document.getElementById('total_debt_outstanding').value),
    income: Number(document.getElementById('income').value),
    years_employed: Number(document.getElementById('years_employed').value),
    fico_score: Number(document.getElementById('fico_score').value),
  };
}

function showResult(data) {
  const result = document.getElementById('result');
  result.classList.remove('hidden');

  const badge = document.getElementById('result-badge');
  badge.textContent = `Rating ${data.credit_rating} · ${data.risk_label} risk`;
  badge.className = `badge r${data.credit_rating}`;

  document.getElementById('result-customer').textContent = `Customer #${data.customer_id}`;
  document.getElementById('result-pd').textContent = pct(data.prob_default);
  document.getElementById('result-rating').textContent = `${data.credit_rating} / 6`;
  document.getElementById('result-el').textContent = money(data.expected_loss);

  document.getElementById('result-note').textContent = data.saved_to_db
    ? 'Saved to the database and included in portfolio insights below.'
    : 'Prediction complete, but the database was unreachable — this result was not saved.';
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const errorBox = document.getElementById('form-error');
  errorBox.classList.add('hidden');

  const submitBtn = e.target.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Scoring…';

  try {
    const payload = readForm();
    const data = await getJSON('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    showResult(data);
    loadInsights();
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove('hidden');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Score borrower';
  }
}

// ---------------------------------------------------------------- insights

async function loadOverview() {
  const o = await getJSON('/api/analytics/overview');
  document.getElementById('kpi-total-loans').textContent = o.total_loans.toLocaleString();
  document.getElementById('kpi-total-scored').textContent = o.total_scored.toLocaleString();
  document.getElementById('kpi-avg-pd').textContent = pct(o.avg_prob_default);
  document.getElementById('kpi-total-el').textContent = money(o.total_expected_loss);
  document.getElementById('kpi-high-risk').textContent =
    o.high_risk_pct === null ? '—' : `${o.high_risk_pct}%`;
}

async function loadFicoChart() {
  const buckets = await getJSON('/api/analytics/fico-buckets');
  const ctx = document.getElementById('fico-chart');
  const data = {
    labels: buckets.map(b => b.bucket),
    datasets: [{
      label: 'Default rate %',
      data: buckets.map(b => b.default_rate_pct),
      backgroundColor: '#1f5c66',
      borderRadius: 4,
    }],
  };
  if (ficoChart) { ficoChart.data = data; ficoChart.update(); return; }
  ficoChart = new Chart(ctx, {
    type: 'bar',
    data,
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { callback: v => v + '%' } } },
    },
  });
}

async function loadRatingChart() {
  const rows = await getJSON('/api/analytics/rating-breakdown');
  const emptyNote = document.getElementById('rating-empty');
  const canvas = document.getElementById('rating-chart');

  if (rows.length === 0) {
    emptyNote.classList.remove('hidden');
    canvas.classList.add('hidden');
    return;
  }
  emptyNote.classList.add('hidden');
  canvas.classList.remove('hidden');

  const data = {
    labels: rows.map(r => r.risk_label),
    datasets: [{
      label: 'Borrowers',
      data: rows.map(r => r.borrowers),
      backgroundColor: rows.map(r => RISK_COLORS[r.rating]),
      borderRadius: 4,
    }],
  };
  if (ratingChart) { ratingChart.data = data; ratingChart.update(); return; }
  ratingChart = new Chart(canvas, {
    type: 'bar',
    data,
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

async function loadTopRisk() {
  const rows = await getJSON('/api/analytics/top-risk?limit=10');
  const body = document.getElementById('top-risk-body');

  if (rows.length === 0) {
    body.innerHTML = '<tr><td colspan="6" class="empty-note">No borrowers scored yet.</td></tr>';
    return;
  }

  body.innerHTML = rows.map(r => `
    <tr>
      <td>${r.customer_id}</td>
      <td>${r.fico_score}</td>
      <td>${money(r.income)}</td>
      <td>${pct(r.prob_default)}</td>
      <td class="risk-cell">${r.risk_label}</td>
      <td>${money(r.expected_loss)}</td>
    </tr>
  `).join('');
}

async function loadInsights() {
  await Promise.all([loadOverview(), loadFicoChart(), loadRatingChart(), loadTopRisk()]);
}

async function handleScoreAll() {
  const btn = document.getElementById('score-all-btn');
  btn.disabled = true;
  btn.textContent = 'Scoring all loans…';
  try {
    const result = await getJSON('/api/score-all', { method: 'POST' });
    btn.textContent = `Scored ${result.scored} loans ✓`;
    await loadInsights();
  } catch (err) {
    btn.textContent = 'Score all loans';
    alert(err.message);
  } finally {
    btn.disabled = false;
    setTimeout(() => { btn.textContent = 'Score all loans'; }, 2500);
  }
}

// ---------------------------------------------------------------- init

document.getElementById('score-form').addEventListener('submit', handleFormSubmit);
document.getElementById('score-all-btn').addEventListener('click', handleScoreAll);

loadHealth();
loadInsights();
