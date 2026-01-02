const ELEMENTS = {
    grid: document.getElementById('dashboard-grid')
};

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadMonthlyPredictions();
});

async function loadMonthlyPredictions() {
    renderLoader();
    try {
        const response = await fetch('/api/predictions/monthly');
        const result = await response.json();

        if (result.predictions && result.predictions.length > 0) {
            renderMonthlyCards(result.predictions);
        } else {
            showError("No predictions available.");
        }
    } catch (error) {
        showError(error.message);
    }
}

function displayLastUpdated(timestamp) {
    const footer = document.createElement('div');
    footer.style.cssText = 'grid-column: 1/-1; text-align: center; padding: 2rem 0; color: var(--text-muted); font-size: 0.85rem; border-top: 1px solid var(--glass-border); margin-top: 2rem;';

    const date = new Date(timestamp);
    const formattedDate = date.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });

    footer.innerHTML = `<i class="fa-solid fa-clock"></i> <strong>Last Updated:</strong> ${formattedDate} <span style="margin-left: 1rem; opacity: 0.7;">(Backend Pipeline Last Run)</span>`;
    ELEMENTS.grid.appendChild(footer);
}

function renderMonthlyCards(predictions) {
    ELEMENTS.grid.innerHTML = '';

    predictions.forEach(item => {
        const symbol = item.symbol;
        const price = item.current_price;
        const pred = item.prediction;

        const isUp = pred.direction === 'UP';
        const isDown = pred.direction === 'DOWN';
        const badgeClass = isUp ? 'badge-up' : (isDown ? 'badge-down' : 'badge-neutral');
        const borderStyle = isUp ? 'border-left: 4px solid var(--accent-green);' : (isDown ? 'border-left: 4px solid var(--accent-red);' : '');

        const card = document.createElement('div');
        card.className = 'card';
        card.style = borderStyle;

        // Confidence bar instead of circular gauge
        const confidence = pred.confidence_score || 5;
        const confidencePercent = (confidence / 10) * 100;
        const confidenceClass = confidence >= 7 ? 'high' : confidence >= 5 ? 'medium' : 'low';

        // Fundamental Rating
        let fundColor = '#888';
        if (pred.fundamental_rating && pred.fundamental_rating.includes('BUY')) fundColor = 'var(--accent-green)';
        if (pred.fundamental_rating && pred.fundamental_rating.includes('SELL')) fundColor = 'var(--accent-red)';

        const fundBadge = `
            <div style="background: rgba(255,255,255,0.05); border-radius: 4px; padding: 4px 8px; font-size: 0.75rem; color: ${fundColor}; font-weight: 600; text-transform: uppercase;">
                <i class="fa-solid fa-building"></i> ${pred.fundamental_rating || 'N/A'}
            </div>
        `;

        card.innerHTML = `
            <div class="card-header">
                <div class="company-info">
                    <h2>${symbol}</h2>
                    <div style="font-size: 0.75rem; color: var(--accent-color); margin-top: 2px;">
                        <i class="fa-regular fa-clock"></i> Target: ${pred.target_date || 'N/A'}
                    </div>
                </div>
                <div class="prediction-badge ${badgeClass}">${pred.direction}</div>
            </div>
            <div class="price-section">
                <div class="current-price">₹${price ? price.toLocaleString() : '---'}</div>
                <div class="price-details">
                    ${fundBadge}
                </div>
            </div>

            <div class="confidence-bar">
                <div class="confidence-label">
                    <span style="font-weight: 600; color: var(--text-primary)">Confidence</span>
                    <span style="font-weight: 700; color: var(--accent-green)">
                        ${confidence}/10
                    </span>
                </div>
                <div class="confidence-track">
                    <div class="confidence-fill ${confidenceClass}" style="width: ${confidencePercent}%"></div>
                </div>
            </div>
            
            <div class="prediction-stats">
                <div class="stat-box">
                    <div class="stat-label">Month High Target</div>
                    <div class="stat-value" style="font-size: 1rem; color: var(--accent-green);">
                        ₹${pred.month_high_target || '?'}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Month Low Target</div>
                    <div class="stat-value" style="font-size: 1rem; color: var(--accent-red);">
                        ₹${pred.month_low_target || '?'}
                    </div>
                </div>
            </div>

            <div class="prediction-stats">
                <div class="stat-box">
                    <div class="stat-label">Expected Move</div>
                    <div class="stat-value" style="font-size: 1rem;">
                        ${pred.predicted_move ? (Math.abs(pred.predicted_move).toFixed(2) + '%') : 'N/A'}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Probability</div>
                    <div class="stat-value" style="font-size: 1rem;">
                        ${pred.probability ? (pred.probability * 100).toFixed(0) + '%' : 'N/A'}
                    </div>
                </div>
            </div>

            <div class="rationale-box">
                <div class="rationale-header">📈 Fundamental & Macro</div>
                ${pred.rationale || 'Analysis not available.'}
            </div>
        `;
        ELEMENTS.grid.appendChild(card);
    });
}

function renderLoader() { ELEMENTS.grid.innerHTML = `<div class="loader"><div class="spinner"></div><p>Loading Monthly...</p></div>`; }
function showError(msg) { ELEMENTS.grid.innerHTML = `<div class="loader" style="color:red"><p>${msg}</p></div>`; }
async function triggerPipeline() { await fetch('/api/refresh', { method: 'POST' }); alert("Running pipeline..."); }
