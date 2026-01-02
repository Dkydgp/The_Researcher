const ELEMENTS = {
    grid: document.getElementById('dashboard-grid'),
    refreshBtn: document.getElementById('refresh-btn'),
    lastUpdated: document.getElementById('last-updated'),
    navItems: document.querySelectorAll('.nav-item'),
    historyControls: document.getElementById('history-controls'),
    viewTitle: document.getElementById('view-title'),
    viewSubtitle: document.getElementById('view-subtitle'),
    dateSelect: document.getElementById('history-date-select'),
    marketState: document.getElementById('market-state')
};

const state = {
    currentView: 'live' // 'live' or 'history'
};

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadLiveData();
});

function switchView(view) {
    state.currentView = view;

    // Update Nav UI
    ELEMENTS.navItems.forEach(item => item.classList.remove('active'));
    if (view === 'live') {
        ELEMENTS.navItems[0].classList.add('active');
        ELEMENTS.historyControls.classList.add('hidden');
        ELEMENTS.refreshBtn.style.display = 'block';
        ELEMENTS.viewTitle.innerText = "Market Overview";
        ELEMENTS.viewSubtitle.innerText = "Real-time AI analysis of top NIFTY 50 constituents";
        loadLiveData();
    } else {
        ELEMENTS.navItems[1].classList.add('active');
        ELEMENTS.historyControls.classList.remove('hidden');
        ELEMENTS.refreshBtn.style.display = 'none';
        ELEMENTS.viewTitle.innerText = "Analysis Archive";
        ELEMENTS.viewSubtitle.innerText = "Historical AI predictions and outcomes";
        loadHistoryDates();
    }
}

async function loadLiveData() {
    renderLoader();
    try {
        const response = await fetch('/api/latest');
        const result = await response.json();

        if (result.status === 'success') {
            ELEMENTS.lastUpdated.innerText = `Updated: ${result.last_updated}`;

            // Display market context if available
            if (result.market_context) {
                displayMarketContext(result.market_context);
            }

            renderCards(result.data);
            updateMarketStatus(result.last_updated);
        }
    } catch (error) {
        showError(error.message);
    }
}

function displayMarketContext(mkt) {
    const subtitle = document.getElementById('view-subtitle');
    if (subtitle && mkt.nifty_trend) {
        const trendColor = mkt.nifty_trend === 'BULL' ? '#00ff88' : mkt.nifty_trend === 'BEAR' ? '#ff4757' : '#888';
        const volColor = mkt.volatility_regime === 'HIGH' ? '#ff4757' : mkt.volatility_regime === 'LOW' ? '#00ff88' : '#FFB800';

        subtitle.innerHTML = `
            Real-time AI analysis | 
            🌍 S&P: <span style="color: ${mkt.sp500_change >= 0 ? '#00ff88' : '#ff4757'}">${mkt.sp500_change > 0 ? '+' : ''}${mkt.sp500_change ? mkt.sp500_change.toFixed(2) : 'N/A'}%</span> | 
            🛢️ Oil: $${mkt.crude_oil ? mkt.crude_oil.toFixed(2) : 'N/A'} | 
            📊 Market: <span style="color: ${trendColor}">${mkt.nifty_trend || 'UNKNOWN'}</span> / 
            <span style="color: ${volColor}">${mkt.volatility_regime || 'UNKNOWN'} Vol</span>
        `;
    }
}

async function loadHistoryDates() {
    try {
        const response = await fetch('/api/history/dates');
        const data = await response.json();
        const dates = data.dates || [];

        ELEMENTS.dateSelect.innerHTML = '<option value="">Select Date...</option>';
        dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.innerText = new Date(date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' });
            ELEMENTS.dateSelect.appendChild(option);
        });

        if (dates.length > 0) {
            ELEMENTS.dateSelect.value = dates[0];
            loadHistoryDate();
        } else {
            ELEMENTS.grid.innerHTML = '<div class="loader"><p>No history available yet.</p></div>';
        }
    } catch (error) {
        showError("Failed to load history dates");
    }
}

async function loadHistoryDate() {
    const date = ELEMENTS.dateSelect.value;
    if (!date) return;

    renderLoader();
    try {
        const response = await fetch(`/api/history/${date}`);
        const result = await response.json();

        if (result.data) {
            const formattedData = result.data.map(item => ({
                symbol: item.symbol,
                short_name: item.symbol.split(' ')[0],
                is_index: false,
                price: {
                    close: item.market_data.close,
                    open: item.market_data.open
                },
                fundamentals: {},
                prediction: item.prediction
            }));
            renderCards(formattedData, true);
        }
    } catch (error) {
        showError("Failed to load history data");
    }
}

function renderCards(companies, isHistory = false) {
    ELEMENTS.grid.innerHTML = '';

    companies.forEach(({ company, symbol, short_name, is_index, prediction: pred, price, fundamentals: fund }) => {
        // Handle both formats (live and history)
        const companyName = company ? company.symbol : symbol;
        const companyShort = company ? company.short_name : short_name;
        const isIndexStock = company ? company.is_index : is_index;
        const prediction = pred || { direction: 'NEUTRAL', predicted_percentage_move: 0, confidence_score: 5, rationale: 'No prediction available.' };
        const priceData = price || { close: 0, open: 0 };
        const fundamentals = fund || { stock_pe: '-', roce: '-' };

        // Performance calculation for history
        let performanceHtml = '';
        if (isHistory && priceData.open && priceData.close) {
            const actualMovePercent = ((priceData.close - priceData.open) / priceData.open) * 100;
            const actualDirection = actualMovePercent > 0 ? 'UP' : (actualMovePercent < 0 ? 'DOWN' : 'NEUTRAL');

            let predictionCorrect = false;
            if (prediction.direction === 'UP' && actualDirection === 'UP') predictionCorrect = true;
            if (prediction.direction === 'DOWN' && actualDirection === 'DOWN') predictionCorrect = true;
            if (prediction.direction === 'NEUTRAL' && Math.abs(actualMovePercent) < 0.2) predictionCorrect = true;

            const resultIcon = predictionCorrect ? '<i class="fa-solid fa-circle-check text-green"></i>' : '<i class="fa-solid fa-circle-xmark text-red"></i>';
            const resultClass = predictionCorrect ? 'text-green' : 'text-red';
            const moveClass = actualMovePercent >= 0 ? 'up-color' : 'down-color';

            performanceHtml = `
                <div class="performance-comparison" style="margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.85rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="color: var(--text-secondary)">Actual Move:</span>
                        <span class="${moveClass}" style="font-weight: 600">
                            ${actualMovePercent > 0 ? '+' : ''}${actualMovePercent.toFixed(2)}%
                        </span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: var(--text-secondary)">Accuracy:</span>
                        <span class="${resultClass}" style="font-weight: 600;">
                            ${resultIcon} ${predictionCorrect ? 'Correct' : 'Missed'}
                        </span>
                    </div>
                </div>
            `;
        }

        const isUp = prediction.direction === 'UP';
        const isDown = prediction.direction === 'DOWN';

        const badgeClass = isUp ? 'badge-up' : (isDown ? 'badge-down' : 'badge-neutral');
        const icon = isUp ? 'fa-arrow-trend-up' : (isDown ? 'fa-arrow-trend-down' : 'fa-minus');
        const textClass = isUp ? 'up-color' : (isDown ? 'down-color' : '');
        const borderStyle = isUp ? 'border-left: 4px solid var(--accent-green);' : (isDown ? 'border-left: 4px solid var(--accent-red);' : '');

        const card = document.createElement('div');
        card.className = 'card';
        if (isHistory) card.style = borderStyle;

        // Generate circular gauge and probability visualization
        const circularGauge = createCircularGauge(prediction.confidence_score, 10);
        const probabilityVis = prediction.daily_probability
            ? createProbabilityBar(prediction.daily_probability, prediction.daily_direction)
            : '';

        card.innerHTML = `
            <div class="card-header">
                <div class="company-info">
                    <h2>${companyShort}</h2>
                    <span class="symbol">${companyName}</span>
                </div>
                <div class="prediction-badge ${badgeClass}">${prediction.direction}</div>
            </div>
            
            <div class="price-section">
                <div class="current-price">₹${priceData.close ? priceData.close.toLocaleString() : '---'}</div>
                <div class="price-details">
                    <div class="price-row">
                        <span>O:</span> ${priceData.open ? priceData.open.toLocaleString() : '-'}
                    </div>
                    <div class="price-row">
                        <span>C:</span> ${priceData.close ? priceData.close.toLocaleString() : '-'}
                    </div>
                </div>
            </div>

            ${circularGauge}
            ${probabilityVis}

            <div class="prediction-value" style="margin-top: 1rem;">
                ${prediction.weekly_trend ? `
                <div style="margin-bottom: 1rem; padding: 0.8rem; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid ${prediction.weekly_trend === 'UP' ? 'var(--accent-green)' : prediction.weekly_trend === 'DOWN' ? 'var(--accent-red)' : '#888'}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem">
                        <span style="color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase">📅 Weekly Outlook</span>
                        <span style="font-weight: 700; color: ${prediction.weekly_trend === 'UP' ? 'var(--accent-green)' : prediction.weekly_trend === 'DOWN' ? 'var(--accent-red)' : '#888'}">${prediction.weekly_trend}</span>
                    </div>
                    <div style="font-size: 0.85rem">
                        Range: <span class="${prediction.weekly_range_min >= 0 ? 'up-color' : 'down-color'}">${prediction.weekly_range_min > 0 ? '+' : ''}${prediction.weekly_range_min}%</span> to 
                        <span class="${prediction.weekly_range_max >= 0 ? 'up-color' : 'down-color'}">${prediction.weekly_range_max > 0 ? '+' : ''}${prediction.weekly_range_max}%</span>
                    </div>
                </div>
                ` : ''}

                <div class="pred-percent ${textClass}">
                    <i class="fas ${icon}"></i>
                    ${prediction.daily_direction ? `
                        <span>
                            <strong>${prediction.daily_direction}</strong> tomorrow
                        </span>
                    ` : `
                        <span>${prediction.predicted_percentage_move}% Predicted</span>
                    `}
                </div>

                ${prediction.daily_range_min !== undefined && prediction.daily_range_max !== undefined ? `
                <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.4rem">
                    Expected range: <span class="${prediction.daily_range_min >= 0 ? 'up-color' : 'down-color'}">${prediction.daily_range_min > 0 ? '+' : ''}${prediction.daily_range_min}%</span> to 
                    <span class="${prediction.daily_range_max >= 0 ? 'up-color' : 'down-color'}">${prediction.daily_range_max > 0 ? '+' : ''}${prediction.daily_range_max}%</span>
                </p>
                ` : ''}

                ${performanceHtml}
            </div>

            ${!isHistory && !isIndexStock && fundamentals.stock_pe ? `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; font-size: 0.85rem">
                <div>
                    <span style="color: var(--text-secondary)">P/E</span>
                    <div style="font-weight: 600">${fundamentals.stock_pe}</div>
                </div>
                <div>
                    <span style="color: var(--text-secondary)">ROCE</span>
                    <div style="font-weight: 600">${fundamentals.roce}%</div>
                </div>
            </div>
            ` : ''}

            <div class="rationale-box">
                <div class="rationale-header">🧠 AI Analysis</div>
                ${prediction.rationale || 'Analysis not available.'}
            </div>
        `;
        ELEMENTS.grid.appendChild(card);
    });
}

async function triggerPipeline() {
    const btn = ELEMENTS.refreshBtn;
    const originalText = btn.innerHTML;

    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running Pipeline...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/refresh', { method: 'POST' });
        const result = await response.json();

        if (result.status === 'started') {
            alert("Pipeline started! This will take about a minute. The dashboard will update automatically when you refresh.");
        }
    } catch (e) {
        alert("Error starting pipeline: " + e.message);
    } finally {
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }, 2000);
    }
}

function renderLoader() {
    ELEMENTS.grid.innerHTML = `
        <div class="loader">
            <div class="spinner"></div>
            <p>Processing Market Data...</p>
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

function updateMarketStatus(dateStr) {
    const now = new Date();
    const hour = now.getHours();

    if (hour >= 9 && hour < 16) {
        ELEMENTS.marketState.innerText = "Market Open";
        document.querySelector('.dot').style.backgroundColor = "var(--accent-green)";
    } else {
        ELEMENTS.marketState.innerText = "Market Closed";
        document.querySelector('.dot').style.backgroundColor = "var(--text-secondary)";
    }
}
