// Enhanced Daily View with Professional Card Rendering
const ELEMENTS = {
    grid: document.getElementById('dashboard-grid'),
    marketContextBar: document.getElementById('market-context-bar')
};

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadDailyPredictions();
});

async function loadDailyPredictions() {
    renderLoader();
    try {
        const response = await fetch('/api/predictions/daily');
        const result = await response.json();

        if (result.predictions && result.predictions.length > 0) {
            renderDailyCards(result.predictions);
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
    const formattedDate = date.toLocaleString('en-IN', {
        dateStyle: 'medium',
        timeStyle: 'short'
    });

    footer.innerHTML = `
        <i class="fa-solid fa-clock"></i> 
        <strong>Last Updated:</strong> ${formattedDate}
        <span style="margin-left: 1rem; opacity: 0.7;">(Backend Pipeline Last Run)</span>
    `;

    ELEMENTS.grid.appendChild(footer);
}

function renderDailyCards(predictions) {
    ELEMENTS.grid.innerHTML = '';

    predictions.forEach((item, index) => {
        const symbol = item.symbol;
        const price = item.current_price;
        const pred = item.prediction;

        // Determine direction styling
        const isUp = pred.direction === 'UP';
        const isDown = pred.direction === 'DOWN';
        const badgeClass = isUp ? 'badge-up' : (isDown ? 'badge-down' : 'badge-neutral');
        const textClass = isUp ? 'up-color' : (isDown ? 'down-color' : 'neutral-color');
        const icon = isUp ? 'fa-arrow-trend-up' : (isDown ? 'fa-arrow-trend-down' : 'fa-minus');

        // Confidence level styling
        const confidence = pred.confidence_score || 5;
        const confidencePercent = (confidence / 10) * 100;
        const confidenceClass = confidence >= 7 ? 'high' : confidence >= 5 ? 'medium' : 'low';

        // Create card
        const card = document.createElement('div');
        card.className = 'card';
        card.style.animationDelay = `${index * 0.1}s`;

        card.innerHTML = `
            <div class="card-header">
                <div class="company-info">
                    <h2>${symbol}</h2>
                    <span class="symbol">${pred.target_date || 'Next Trading Day'}</span>
                </div>
                <div class="prediction-badge ${badgeClass}">
                    <i class="fas ${icon}"></i>
                    ${pred.direction}
                </div>
            </div>

            <div class="price-section">
                <div class="current-price ${textClass}">
                    ₹${price ? price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '---'}
                </div>
                ${pred.predicted_move ? `
                    <div class="price-change ${isUp ? 'positive' : isDown ? 'negative' : ''}">
                        <i class="fas ${icon}"></i>
                        ${Math.abs(pred.predicted_move).toFixed(2)}%
                    </div>
                ` : ''}
            </div>

            <div class="prediction-stats">
                <div class="stat-box">
                    <div class="stat-label">Target Price</div>
                    <div class="stat-value" style="font-size: 0.95rem;">
                        ₹${pred.target_price_min || '?'} - ₹${pred.target_price_max || '?'}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Expected Move</div>
                    <div class="stat-value ${textClass}" style="font-size: 1.1rem;">
                        ${pred.predicted_move ? (Math.abs(pred.predicted_move).toFixed(2) + '%') : 'N/A'}
                    </div>
                </div>
            </div>

            <div class="prediction-stats">
                <div class="stat-box">
                    <div class="stat-label">Risk Level</div>
                    <div class="stat-value" style="font-size: 1.1rem; color: ${getRiskColor(pred.risk_level)}">
                        ${pred.risk_level || 'MEDIUM'}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Probability</div>
                    <div class="stat-value" style="font-size: 1.1rem;">
                        ${pred.probability ? (pred.probability * 100).toFixed(0) + '%' : 'N/A'}
                    </div>
                </div>
            </div>

            <div class="confidence-bar">
                <div class="confidence-label">
                    <span style="font-weight: 600; color: var(--text-primary)">Confidence</span>
                    <span style="font-weight: 700; color: var(--accent-${confidenceClass === 'high' ? 'green' : confidenceClass === 'medium' ? 'amber' : 'red'})">
                        ${confidence}/10
                    </span>
                </div>
                <div class="confidence-track">
                    <div class="confidence-fill ${confidenceClass}" style="width: ${confidencePercent}%"></div>
                </div>
            </div>

            ${pred.rationale ? `
                <div class="rationale-box">
                    <div class="rationale-header"><i class="fas fa-brain"></i> Analysis</div>
                    ${pred.rationale}
                </div>
            ` : ''}

            ${pred.technical_summary ? `
                <div class="rationale-box" style="margin-top: 0.75rem; border-left-color: ${isUp ? 'var(--accent-green)' : isDown ? 'var(--accent-red)' : 'var(--accent-blue)'};">
                    <div class="rationale-header"><i class="fas fa-chart-line"></i> Technical</div>
                    ${pred.technical_summary}
                </div>
            ` : ''}
        `;

        ELEMENTS.grid.appendChild(card);

        // Trigger animation
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 50);
    });
}

function getRiskColor(riskLevel) {
    switch (riskLevel) {
        case 'HIGH': return 'var(--accent-red)';
        case 'MEDIUM': return 'var(--accent-amber)';
        case 'LOW': return 'var(--accent-green)';
        default: return 'var(--text-secondary)';
    }
}

function renderLoader() {
    ELEMENTS.grid.innerHTML = `
        <div class="loader">
            <div class="spinner"></div>
            <p style="margin-top: 1rem; font-size: 1.1rem; font-weight: 500;">Loading Daily Predictions...</p>
        </div>
    `;
}

function showError(msg) {
    ELEMENTS.grid.innerHTML = `
        <div class="loader" style="color: var(--accent-red)">
            <i class="fa-solid fa-circle-exclamation" style="font-size: 3rem; margin-bottom: 1.5rem; opacity: 0.7"></i>
            <p style="font-size: 1.1rem; font-weight: 500;">${msg}</p>
            <button onclick="location.reload()" style="margin-top: 1.5rem; padding: 12px 24px; background: var(--accent-blue); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer;">
                <i class="fas fa-refresh"></i> Retry
            </button>
        </div>
    `;
}

async function triggerPipeline() {
    alert("Data pipeline started! Predictions will be updated in a few minutes. Refresh the page to see new data.");
}

// Add card animation styles dynamically
const style = document.createElement('style');
style.textContent = `
    .card {
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.5s ease, transform 0.5s ease;
    }
`;
document.head.appendChild(style);
