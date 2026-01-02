// Danelfin-style UI enhancements

// Generate circular AI Score gauge (Danelfin-style)
function createCircularGauge(score, maxScore = 10) {
    const percentage = (score / maxScore) * 100;
    const angle = (percentage / 100) * 270; // 270 degrees for 3/4 circle
    const circumference = 2 * Math.PI * 45; // radius = 45
    const offset = circumference - (angle / 360) * circumference;

    // Determine color based on score
    let color, rating;
    if (score >= 9) {
        color = '#22c55e'; // Strong Buy - Green
        rating = 'Strong Buy';
    } else if (score >= 7) {
        color = '#a3e635'; // Buy - Light Green
        rating = 'Buy';
    } else if (score >= 5) {
        color = '#fbbf24'; // Hold - Yellow
        rating = 'Hold';
    } else if (score >= 3) {
        color = '#fb923c'; // Sell - Orange
        rating = 'Sell';
    } else {
        color = '#ef4444'; // Strong Sell - Red
        rating = 'Strong Sell';
    }

    const ratingClass = rating.toLowerCase().replace(/ /g, '-');

    return `
        <div class="ai-score-container">
            <div class="circular-gauge">
                <svg class="gauge-circle" viewBox="0 0 100 100">
                    <circle class="gauge-bg-circle" cx="50" cy="50" r="45"></circle>
                    <circle 
                        class="gauge-progress-circle" 
                        cx="50" 
                        cy="50" 
                        r="45"
                        stroke="${color}"
                        stroke-dasharray="${circumference}"
                        stroke-dashoffset="${offset}"
                    ></circle>
                </svg>
                <div class="gauge-center">
                    <div class="gauge-score" style="color: ${color}">${score}</div>
                    <div class="gauge-max">/10</div>
                </div>
            </div>
        </div>
    `;
}

// Get rating classification
function getRatingFromScore(score) {
    if (score >= 9) return { label: 'Strong Buy', class: 'strong-buy' };
    if (score >= 7) return { label: 'Buy', class: 'buy' };
    if (score >= 5) return { label: 'Hold', class: 'hold' };
    if (score >= 3) return { label: 'Sell', class: 'sell' };
    return { label: 'Strong Sell', class: 'strong-sell' };
}

// Create probability visualization
function createProbabilityBar(probability, direction) {
    const position = probability * 100;
    let color;

    if (probability >= 0.7) color = '#22c55e';
    else if (probability >= 0.5) color = '#a3e635';
    else if (probability >= 0.3) color = '#fbbf24';
    else color = '#ef4444';

    return `
        <div class="probability-visual">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 0.75rem; color: var(--text-secondary)">Probability</span>
                <span style="font-size: 0.9rem; font-weight: 700; color: ${color}">${(probability * 100).toFixed(0)}%</span>
            </div>
            <div class="prob-bar-container">
                <div class="prob-indicator" style="left: ${position}%; border-color: ${color}"></div>
            </div>
            <div class="prob-labels">
                <span>Low (0%)</span>
                <span>High (100%)</span>
            </div>
        </div>
    `;
}

// Create pattern badges
function createPatternBadges(patterns) {
    if (!patterns || patterns.length === 0) return '';

    return `
        <div class="patterns-container">
            ${patterns.map(p => {
        const typeClass = p.signal === 'BULLISH' ? 'bullish' : p.signal === 'BEARISH' ? 'bearish' : 'neutral';
        const emoji = p.signal === 'BULLISH' ? '🟢' : p.signal === 'BEARISH' ? '🔴' : '🟡';
        return `<span class="pattern-tag pattern-${typeClass}">${emoji} ${p.pattern.replace(/_/g, ' ')}</span>`;
    }).join('')}
        </div>
    `;
}

// Create metrics row
function createMetricsRow(metrics) {
    return `
        <div class="metrics-row">
            ${metrics.map(m => `
                <div class="metric-box">
                    <div class="metric-title">${m.label}</div>
                    <div class="metric-data" style="color: ${m.color || 'var(--text-primary)'}">${m.value}</div>
                </div>
            `).join('')}
        </div>
    `;
}

// Export for use in main script
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createCircularGauge,
        getRatingFromScore,
        createProbabilityBar,
        createPatternBadges,
        createMetricsRow
    };
}


// --- ARCHIVE MANAGER (Global) ---
document.addEventListener('DOMContentLoaded', () => {
    initArchive();
});

function initArchive() {
    const archiveGrid = document.getElementById('archive-grid');
    const archiveSelect = document.getElementById('archive-date-select');
    const archiveTimeframe = document.getElementById('archive-timeframe-select');

    if (!archiveGrid || !archiveSelect) return; // Exit if basics missing

    // Initial Load
    loadArchiveDates(archiveSelect, archiveTimeframe);

    // Listeners
    if (archiveTimeframe) {
        archiveTimeframe.addEventListener('change', () => {
            loadArchiveDates(archiveSelect, archiveTimeframe);
            archiveGrid.innerHTML = '<div style="color: var(--text-secondary); grid-column: 1/-1; text-align: center; padding: 2rem;">Select a date to view history.</div>';
        });
    }

    archiveSelect.addEventListener('change', (e) => {
        if (e.target.value) {
            const tf = archiveTimeframe ? archiveTimeframe.value : 'DAILY';
            loadArchiveData(e.target.value, archiveGrid, tf);
        }
    });
}

async function loadArchiveDates(select, timeframeEl) {
    const tf = timeframeEl ? timeframeEl.value : 'DAILY';
    select.innerHTML = '<option value="">Loading...</option>';

    try {
        const res = await fetch(`/api/history/dates?timeframe=${tf}`);
        const data = await res.json();
        select.innerHTML = '<option value="">Select Date...</option>';

        if (data.dates && data.dates.length > 0) {
            data.dates.forEach(date => {
                const opt = document.createElement('option');
                opt.value = date;
                opt.innerText = date;
                select.appendChild(opt);
            });
        } else {
            const opt = document.createElement('option');
            opt.innerText = "No dates found";
            select.appendChild(opt);
        }
    } catch (e) {
        console.error("Failed to load archive dates", e);
        select.innerHTML = '<option value="">Error</option>';
    }
}

async function loadArchiveMetrics(timeframe) {
    const metricsPanel = document.getElementById('metrics-panel');
    if (!metricsPanel) return;

    try {
        const res = await fetch(`/api/archive/metrics?timeframe=${timeframe}`);
        const metrics = await res.json();

        // Show metrics panel
        metricsPanel.style.display = 'block';

        // Update overall accuracy (with null checks)
        const sentimentAccEl = document.getElementById('sentiment-accuracy');
        const priceAccEl = document.getElementById('price-accuracy');
        const totalPredEl = document.getElementById('total-predictions');
        const sentimentTotalEl = document.getElementById('sentiment-total');

        if (sentimentAccEl) sentimentAccEl.textContent = `${metrics.overall_accuracy.sentiment_accuracy}%`;
        if (priceAccEl) priceAccEl.textContent = `${metrics.overall_accuracy.price_accuracy}%`;
        if (totalPredEl) totalPredEl.textContent = metrics.overall_accuracy.total_predictions;
        if (sentimentTotalEl) sentimentTotalEl.textContent = `${metrics.overall_accuracy.total_predictions} predictions`;

        // Update confidence correlation (with null checks)
        if (metrics.confidence_correlation) {
            const highAcc = metrics.confidence_correlation.high_confidence_accuracy || 0;
            const mediumAcc = metrics.confidence_correlation.medium_confidence_accuracy || 0;
            const lowAcc = metrics.confidence_correlation.low_confidence_accuracy || 0;

            const highConfAccEl = document.getElementById('high-conf-accuracy');
            const mediumConfAccEl = document.getElementById('medium-conf-accuracy');
            const lowConfAccEl = document.getElementById('low-conf-accuracy');
            const highBarEl = document.getElementById('high-conf-bar');
            const mediumBarEl = document.getElementById('medium-conf-bar');
            const lowBarEl = document.getElementById('low-conf-bar');

            if (highConfAccEl) highConfAccEl.textContent = `${highAcc.toFixed(1)}%`;
            if (mediumConfAccEl) mediumConfAccEl.textContent = `${mediumAcc.toFixed(1)}%`;
            if (lowConfAccEl) lowConfAccEl.textContent = `${lowAcc.toFixed(1)}%`;

            if (highBarEl) highBarEl.style.width = `${highAcc}%`;
            if (mediumBarEl) mediumBarEl.style.width = `${mediumAcc}%`;
            if (lowBarEl) lowBarEl.style.width = `${lowAcc}%`;
        }
    } catch (e) {
        console.error("Failed to load metrics", e);
        metricsPanel.style.display = 'none';
    }
}

async function loadArchiveData(date, grid, timeframe) {
    grid.innerHTML = '<div class="loader"><div class="spinner"></div><p>Loading History...</p></div>';

    // Load metrics when loading archive data
    loadArchiveMetrics(timeframe);

    try {
        const res = await fetch(`/api/history/${date}?timeframe=${timeframe}`);
        const result = await res.json();

        if (result.data) {
            renderArchiveCards(result.data, date, timeframe, grid);
        } else {
            grid.innerHTML = '<p>No data found for this date.</p>';
        }
    } catch (e) {
        grid.innerText = "Error loading history.";
    }
}

function renderArchiveCards(data, date, timeframe, grid) {
    grid.innerHTML = '';

    data.forEach(item => {
        const pred = item.prediction;
        const market = item.market_data;

        const card = document.createElement('div');
        card.className = 'card';
        card.style = "opacity: 0.8; border: 1px solid rgba(255,255,255,0.1);";

        if (timeframe === 'DAILY') {
            // Calculate actual price movement
            const actualMove = market.close && market.open
                ? ((market.close - market.open) / market.open * 100).toFixed(2)
                : null;

            const predictedMove = parseFloat(pred.predicted_move) || 0;

            // Sentiment accuracy: both moved in same direction
            const predictedDirection = predictedMove >= 0 ? 'UP' : 'DOWN';
            const actualDirection = actualMove >= 0 ? 'UP' : 'DOWN';
            const sentimentCorrect = predictedDirection === actualDirection;

            // Price accuracy: predicted % is close to actual % (within 0.5% tolerance)
            const priceCorrect = actualMove !== null
                ? Math.abs(predictedMove - parseFloat(actualMove)) <= 0.5
                : null;

            // Only show sentiment badge if we have actual market data
            const sentimentBadge = actualMove === null
                ? '<span style="color: gray; font-size: 0.75rem;">⏳ Pending</span>'
                : sentimentCorrect
                    ? '<span style="background: rgba(34, 197, 94, 0.2); color: #22c55e; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">✅ Sentiment</span>'
                    : '<span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">❌ Sentiment</span>';

            const priceBadge = priceCorrect === null
                ? '<span style="color: gray; font-size: 0.75rem;">⏳ Pending</span>'
                : priceCorrect
                    ? '<span style="background: rgba(34, 197, 94, 0.2); color: #22c55e; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">✅ Price Move</span>'
                    : '<span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem;">❌ Price Move</span>';

            card.innerHTML = `
                <div class="card-header">
                    <h3>${item.symbol}</h3>
                    <div style="font-size: 0.8rem; color: var(--text-secondary)">${date}</div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; font-size: 0.85rem;">
                    <div style="color: var(--text-secondary);">Prev Close:</div>
                    <div style="text-align: right; font-weight: 600;">₹${market.prev_close ? market.prev_close.toFixed(2) : market.open?.toFixed(2) || 'N/A'}</div>
                    <div style="color: var(--text-secondary);">Confidence:</div>
                    <div style="text-align: right; font-weight: 600; color: var(--accent-color);">${pred.confidence_score || 'N/A'}</div>
                </div>

                <div class="prediction-badge" style="margin: 10px 0;">
                    Predicted: ${predictedMove >= 0 ? '+' : ''}${predictedMove}%
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9rem; margin-bottom: 10px;">
                    <div>Open: ₹${market.open ? market.open.toFixed(2) : 'N/A'}</div>
                    <div>Close: ₹${market.close ? market.close.toFixed(2) : 'N/A'}</div>
                </div>

                ${actualMove !== null ? `
                    <div style="font-size: 0.85rem; color: ${actualMove >= 0 ? '#22c55e' : '#ef4444'}; margin-bottom: 10px; font-weight: 600;">
                        Actual: ${actualMove >= 0 ? '+' : ''}${actualMove}%
                    </div>
                ` : ''}
                
                <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">Accuracy:</span>
                    <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        ${sentimentBadge}
                        ${priceBadge}
                    </div>
                </div>
            `;
        } else {
            // Weekly/Monthly logic (unchanged)
            const isCorrect = (pred.direction === 'UP' && market.close > market.open) ||
                (pred.direction === 'DOWN' && market.close < market.open);

            const statusBadge = isCorrect
                ? '<span style="background: rgba(34, 197, 94, 0.2); color: #22c55e; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">✅ Accurate</span>'
                : '<span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">❌ Missed</span>';

            let targetInfo = '';
            if (timeframe === 'WEEKLY') {
                targetInfo = `Range: ₹${pred.week_low_target} - ₹${pred.week_high_target}`;
            } else {
                targetInfo = `Range: ₹${pred.month_low_target} - ₹${pred.month_high_target}`;
            }

            card.innerHTML = `
                <div class="card-header">
                    <h3>${item.symbol}</h3>
                    <div style="font-size: 0.8rem; color: var(--text-secondary)">${date}</div>
                </div>
                <div class="prediction-badge" style="margin: 10px 0;">Prediction: ${pred.direction}</div>
                
                <div style="font-size: 0.85rem; color: var(--accent-color); margin-bottom: 10px;">${targetInfo}</div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9rem; margin-bottom: 10px;">
                    <div>Open: ₹${market.open ? market.open.toFixed(2) : 'N/A'}</div>
                    <div>Close: ₹${market.close ? market.close.toFixed(2) : 'N/A'}</div>
                </div>
                
                <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <span>Result:</span>
                    ${market.close ? statusBadge : '<span style="color: gray">Pending Market Close</span>'}
                </div>
            `;
        }

        grid.appendChild(card);
    });
}
