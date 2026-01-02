const ELEMENTS = {
    grid: document.getElementById('dashboard-grid'),
    refreshBtn: document.getElementById('refresh-btn'),
    lastUpdated: document.getElementById('last-updated'),
    marketContextBar: document.getElementById('market-context-bar'),
    archiveSelect: document.getElementById('archive-date-select'),
    archiveTimeframe: document.getElementById('archive-timeframe-select'),
    archiveGrid: document.getElementById('archive-grid')
};

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadDailyPredictions();
    loadTodayMetrics();
});

async function loadTodayMetrics() {
    const metricsPanel = document.getElementById('today-metrics-panel');
    if (!metricsPanel) return;

    try {
        // Get today's date in YYYY-MM-DD format
        const today = new Date().toISOString().split('T')[0];

        const res = await fetch(`/api/archive/metrics?timeframe=DAILY&start_date=${today}&end_date=${today}`);
        const metrics = await res.json();

        // Always show panel, update values if we have data
        metricsPanel.style.display = 'block';

        if (metrics.overall_accuracy.total_predictions > 0) {
            document.getElementById('today-sentiment-accuracy').textContent = `${metrics.overall_accuracy.sentiment_accuracy}%`;
            document.getElementById('today-price-accuracy').textContent = `${metrics.overall_accuracy.price_accuracy}%`;
            document.getElementById('today-sentiment-total').textContent = `${metrics.overall_accuracy.total_predictions} stocks`;
            document.getElementById('today-high-conf').textContent = `${metrics.confidence_correlation.high_confidence_accuracy.toFixed(1)}%`;
        } else {
            // Show placeholders if no data yet
            document.getElementById('today-sentiment-accuracy').textContent = '--';
            document.getElementById('today-price-accuracy').textContent = '--';
            document.getElementById('today-sentiment-total').textContent = 'Pending market close';
            document.getElementById('today-high-conf').textContent = '--';
        }
    } catch (e) {
        console.error("Failed to load today's metrics", e);
        // Show panel anyway with error state
        metricsPanel.style.display = 'block';
    }
}


async function loadDailyPredictions() {
    renderLoader();
    try {
        // 1. Fetch Market Context (reused from main API for now or separate)
        // For now we'll just fetch daily predictions

        const response = await fetch('/api/predictions/daily');
        const result = await response.json();

        if (result.predictions) {
            renderDailyCards(result.predictions);
            if (ELEMENTS.lastUpdated) {
                ELEMENTS.lastUpdated.innerText = `Updated: ${new Date().toLocaleTimeString()}`;
            }
        } else {
            showError("No predictions available.");
        }
    } catch (error) {
        showError(error.message);
    }
}

function renderDailyCards(predictions) {
    ELEMENTS.grid.innerHTML = '';

    predictions.forEach(item => {
        const symbol = item.symbol;
        const price = item.current_price;
        const pred = item.prediction;

        // Determine styles based on direction
        const isUp = pred.direction === 'UP';
        const isDown = pred.direction === 'DOWN';
        const badgeClass = isUp ? 'badge-up' : (isDown ? 'badge-down' : 'badge-neutral');
        const borderStyle = isUp ? 'border-left: 4px solid var(--accent-green);' : (isDown ? 'border-left: 4px solid var(--accent-red);' : '');
        const textClass = isUp ? 'up-color' : (isDown ? 'down-color' : '');
        const icon = isUp ? 'fa-arrow-trend-up' : (isDown ? 'fa-arrow-trend-down' : 'fa-minus');

        const card = document.createElement('div');
        card.className = 'card';
        card.style = borderStyle;

        // Use Danelfin UI helpers
        const circularGauge = createCircularGauge(pred.confidence_score, 10);
        const probabilityVis = pred.probability
            ? createProbabilityBar(pred.probability, pred.direction)
            : '';

        card.innerHTML = `
            <div class="card-header">
                <div class="company-info">
                    <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
                        <h2>${symbol}</h2>
                    </div>
                    <div style="font-size: 0.75rem; color: var(--accent-color); margin-top: 2px;">
                        <i class="fa-regular fa-clock"></i> Target: ${pred.target_date || 'N/A'}
                    </div>
                </div>
                <div class="prediction-badge ${badgeClass}">${pred.direction}</div>
            </div>
            
            <div class="price-section">
                <div class="current-price">₹${price ? price.toLocaleString() : '---'}</div>
                <div class="price-details" style="color: var(--text-secondary); font-size: 0.85rem">
                    Target: ₹${pred.target_price_min || '?'} - ₹${pred.target_price_max || '?'}
                </div>
            </div>

            ${circularGauge}
            ${probabilityVis}

            <div class="stats-grid" style="margin-top: 1rem; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.8rem;">
                <div class="stat-item" style="background: rgba(255,255,255,0.05); padding: 8px; border-radius: 6px;">
                    <div style="color: var(--text-secondary)">Risk Level</div>
                    <div style="font-weight: 600; color: ${pred.risk_level === 'HIGH' ? 'var(--accent-red)' : 'var(--text-primary)'}">${pred.risk_level || 'N/A'}</div>
                </div>
                <div class="stat-item" style="background: rgba(255,255,255,0.05); padding: 8px; border-radius: 6px;">
                    <div style="color: var(--text-secondary)">Exp. Move</div>
                    <div style="font-weight: 600; color: ${textClass}">${pred.predicted_move ? pred.predicted_move + '%' : 'N/A'}</div>
                </div>
            </div>

            <div class="rationale-box">
                <div class="rationale-header">🧠 Intra-day Analysis</div>
                ${pred.rationale || 'Analysis not available.'}
            </div>
        `;
        ELEMENTS.grid.appendChild(card);
    });
}

// Reuse helper functions
function renderLoader() {
    ELEMENTS.grid.innerHTML = `
        <div class="loader">
            <div class="spinner"></div>
            <p>Processing Daily Data...</p>
        </div>
    `;
}

function showError(msg) {
    ELEMENTS.grid.innerHTML = `
        <div class="loader" style="color: var(--accent-red)">
            <i class="fa-solid fa-circle-exclamation" style="font-size: 2rem; margin-bottom: 1rem"></i>
            <p>${msg}</p>
        </div>
    `;
}

async function triggerPipeline() {
    const btn = ELEMENTS.refreshBtn;
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running...';
    btn.disabled = true;
    try {
        await fetch('/api/refresh', { method: 'POST' });
        alert("Pipeline started! Check back in a few minutes.");
    } catch (e) {
        alert("Error: " + e.message);
    } finally {
        setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
    }
}

// End of Daily Logic
