// filepath: static/js/dashboard_index.js
document.addEventListener('DOMContentLoaded', function () {
  // Trend Chart
  try {
    const trendCtx = document.getElementById('trend-chart');
    if (trendCtx) {
      new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: ['2018', '2019', '2020', '2021', '2022'],
          datasets: [{
            label: 'PIB (Mds USD)',
            data: [650, 680, 695, 710, 730],
            borderColor: '#2563eb',
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          plugins: { title: { display: true, text: 'Evolution du PIB' } }
        }
      });
    }
  } catch (e) { console.error('trend chart init error', e); }

  // Comparison Chart
  try {
    const comparisonCtx = document.getElementById('comparison-chart');
    if (comparisonCtx) {
      new Chart(comparisonCtx, {
        type: 'line',
        data: {
          labels: ['2018', '2019', '2020', '2021', '2022'],
          datasets: [{
            label: 'Croissance PIB (%)',
            data: [4.8, 5.2, 5.7, 5.4, 5.1],
            borderColor: '#2563eb',
            tension: 0.4
          }, {
            label: 'Inflation (%)',
            data: [1.8, 2.0, 2.3, 2.1, 2.3],
            borderColor: '#e11d48',
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          plugins: { title: { display: true, text: 'Croissance vs Inflation' } }
        }
      });
    }
  } catch (e) { console.error('comparison chart init error', e); }

  // CA chart (data injected via template into window.CA_SERIES)
  try {
    const caEl = document.getElementById('chartCa');
    if (caEl && window.CA_SERIES) {
      const labels = window.CA_SERIES.labels || [];
      const values = window.CA_SERIES.values || [];
      if (labels.length) {
        new Chart(caEl, {
          type: 'line',
          data: { labels, datasets: [{ label: 'CA (EUR)', data: values, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.08)', tension: 0.25, fill: true }] },
          options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { x: { grid: { display: false } }, y: { grid: { color: 'rgba(0,0,0,0.05)' } } }
          }
        });
      }
    }
  } catch (e) { console.error('ca chart init error', e); }
});
