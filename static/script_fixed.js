// Replacement for renderCards function - corrected version

function renderCards_fixed(companies) {
    ELEMENTS.grid.innerHTML = '';

    companies.forEach(({ company, prediction: pred, price, fundamentals: fund }) => {
        const isHistory = state.currentView === 'history';

        const badgeClass = pred.direction === 'UP' ? 'badge-up' : pred.direction === 'DOWN' ? 'badge-down' : 'badge-neutral';
        const textClass = pred.direction === 'UP' ? 'up-color' : pred.direction === 'DOWN' ? 'down-color' : '';
        const icon = pred.direction === 'UP' ? 'fa-arrow-up' : pred.direction === 'DOWN' ? 'fa-arrow-down' : 'fa-minus';

        let performanceHtml = '';
        if (isHistory && pred.actual_open && pred.actual_close) {
            const actual_move = ((pred.actual_close - pred.actual_open) / pred.actual_open * 100).toFixed(2);
            const isCorrect = (pred.direction === 'UP' && actual_move > 0) || (pred.direction === 'DOWN' && actual_move < 0);
            performanceHtml = `
                <div style="margin-top: 0.75rem; padding: 0.75rem; background: ${isCorrect ? 'rgba(35, 134, 54, 0.1)' : 'rgba(218, 54, 51, 0.1)'}; border-radius: 6px;">
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">Actual Movement</div>
                    <div style="font-size: 1rem; font-weight: 700; color: ${actual_move > 0 ? 'var(--accent-green)' : 'var(--accent-red)'};">
                        ${actual_move > 0 ? '+' : ''}${actual_move}%
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.7rem; padding: 4px 8px; background: ${isCorrect ? 'rgba(74, 222, 128, 0.2)' : 'rgba(239, 68, 68, 0.2)'}; border-radius: 4px; display: inline-block;">
                        ${isCorrect ? '✓ CORRECT' : '✗ INCORRECT'}
                    </div>
                </div>
            `;
        }

        const borderStyle = isHistory ? `border-left: 3px solid ${pred.direction === 'UP' ? 'var(--accent-green)' : 'var(--accent-red)'}` : '';

        const card = document.createElement('div');
        card.className = 'card';
        if (isHistory) card.style = borderStyle;

        // Generate circular gauge and probability visualization
        const circularGauge = createCircularGauge(pred.confidence_score, 10);
        const probabilityVis = pred.daily_probability
            ? createProbabilityBar(pred.daily_probability, pred.daily_direction)
            : '';

        card.innerHTML = `
            <div class="card-header">
                <div class="company-info">
                    <h2>${company.symbol}</h2>
                    <span class="symbol">${company.short_name}</span>
                </div>
                <div class="prediction-badge ${badgeClass}">${pred.direction}</div>
            </div>

            <div class="price-section">
                <div class="current-price">₹${price.close ? price.close.toLocaleString() : '---'}</div>
                <div class="price-details">
                    <div class="price-row">
                        <span>O:</span> ${price.open ? price.open.toLocaleString() : '-'}
                    </div>
                    <div class="price-row">
                        <span>C:</span> ${price.close ? price.close.toLocaleString() : '-'}
                    </div>
                </div>
            </div>

            ${circularGauge}
            ${probabilityVis}

            <div class="prediction-value" style="margin-top: 1rem;">
                ${pred.weekly_trend ? `
                <div style="margin-bottom: 1rem; padding: 0.8rem; background: rgba(255,255,255,0.03); border-radius: 8px; border-left: 3px solid ${pred.weekly_trend === 'UP' ? 'var(--accent-green)' : pred.weekly_trend === 'DOWN' ? 'var(--accent-red)' : '#888'}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem">
                        <span style="color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase">📅 Weekly Outlook</span>
                        <span style="font-weight: 700; color: ${pred.weekly_trend === 'UP' ? 'var(--accent-green)' : pred.weekly_trend === 'DOWN' ? 'var(--accent-red)' : '#888'}">${pred.weekly_trend}</span>
                    </div>
                    <div style="font-size: 0.85rem">
                        Range: <span class="${pred.weekly_range_min >= 0 ? 'up-color' : 'down-color'}">${pred.weekly_range_min > 0 ? '+' : ''}${pred.weekly_range_min}%</span> to 
                        <span class="${pred.weekly_range_max >= 0 ? 'up-color' : 'down-color'}">${pred.weekly_range_max > 0 ? '+' : ''}${pred.weekly_range_max}%</span>
                    </div>
                </div>
                ` : ''}

                <div class="pred-percent ${textClass}">
                    <i class="fas ${icon}"></i>
                    ${pred.daily_direction ? `
                        <span>
                            <strong>${pred.daily_direction}</strong> tomorrow
                        </span>
                    ` : `
                        <span>${pred.predicted_percentage_move}% Predicted</span>
                    `}
                </div>

                ${pred.daily_range_min !== undefined && pred.daily_range_max !== undefined ? `
                <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.4rem">
                    Expected range: <span class="${pred.daily_range_min >= 0 ? 'up-color' : 'down-color'}">${pred.daily_range_min > 0 ? '+' : ''}${pred.daily_range_min}%</span> to 
                    <span class="${pred.daily_range_max >= 0 ? 'up-color' : 'down-color'}">${pred.daily_range_max > 0 ? '+' : ''}${pred.daily_range_max}%</span>
                </p>
                ` : ''}

                ${performanceHtml}
            </div>

            ${!isHistory && !company.is_index && fund.stock_pe ? `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; font-size: 0.85rem">
                <div>
                    <span style="color: var(--text-secondary)">P/E</span>
                    <div style="font-weight: 600">${fund.stock_pe}</div>
                </div>
                <div>
                    <span style="color: var(--text-secondary)">ROCE</span>
                    <div style="font-weight: 600">${fund.roce}%</div>
                </div>
            </div>
            ` : ''}

            <div class="rationale-box">
                <div class="rationale-header">🧠 AI Analysis</div>
                ${pred.rationale || 'Analysis not available.'}
            </div>
        `;
        ELEMENTS.grid.appendChild(card);
    });
}
