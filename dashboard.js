// Dashboard JavaScript functionality
let opportunitiesChart = null;
let btcChart = null;
let ethChart = null;

// Initialize dashboard
function initializeDashboard() {
    console.log('🚀 Initializing Crypto Observatory Dashboard');
    
    // Load initial data
    refreshStats();
    refreshOpportunities();
    initializeCharts();
    
    // Set up periodic updates
    setInterval(refreshStats, 30000); // 30 seconds
    setInterval(refreshOpportunities, 60000); // 1 minute
    setInterval(updatePriceCharts, 120000); // 2 minutes
}

// Refresh statistics
function refreshStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatsDisplay(data);
            updateExchangeStatus(data.exchanges || []);
        })
        .catch(error => {
            console.error('Error fetching stats:', error);
            showErrorMessage('Failed to load statistics');
        });
}

// Update statistics display
function updateStatsDisplay(stats) {
    // Uptime
    const uptimeElement = document.getElementById('uptime');
    if (uptimeElement) {
        const days = stats.uptime_days || 0;
        const hours = Math.floor((stats.uptime_hours || 0) % 24);
        uptimeElement.textContent = `${days}d ${hours}h`;
    }
    
    // Total opportunities
    const totalOppsElement = document.getElementById('total-opportunities');
    if (totalOppsElement) {
        totalOppsElement.textContent = formatNumber(stats.total_opportunities || 0);
    }
    
    // Average profit
    const avgProfitElement = document.getElementById('avg-profit');
    if (avgProfitElement) {
        const avgProfit = stats.avg_profit || 0;
        avgProfitElement.textContent = `${avgProfit.toFixed(3)}%`;
        avgProfitElement.className = avgProfit > 0.5 ? 'text-warning' : 'text-success';
    }
    
    // Best opportunity
    const bestOppElement = document.getElementById('best-opportunity');
    if (bestOppElement) {
        const bestProfit = stats.best_opportunity || 0;
        bestOppElement.textContent = `${bestProfit.toFixed(3)}%`;
        bestOppElement.className = bestProfit > 1.0 ? 'text-warning' : 'text-success';
    }
}

// Update exchange status
function updateExchangeStatus(exchanges) {
    const container = document.getElementById('exchange-status');
    if (!container) return;
    
    container.innerHTML = '';
    
    exchanges.forEach(exchange => {
        const col = document.createElement('div');
        col.className = 'col-lg-3 col-md-4 col-sm-6 mb-3';
        
        const isActive = exchange.status === 'active';
        const statusClass = isActive ? 'exchange-active' : 'exchange-inactive';
        const statusIcon = isActive ? 'fas fa-check-circle text-success' : 'fas fa-exclamation-triangle text-warning';
        
        col.innerHTML = `
            <div class="exchange-card ${statusClass}">
                <i class="${statusIcon} fa-2x mb-2"></i>
                <h6 class="text-capitalize">${exchange.name}</h6>
                <small class="text-muted">${isActive ? 'Connected' : 'Disconnected'}</small>
            </div>
        `;
        
        container.appendChild(col);
    });
}

// Refresh opportunities
function refreshOpportunities() {
    const button = document.querySelector('button[onclick="refreshOpportunities()"]');
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
        button.disabled = true;
    }
    
    fetch('/api/opportunities')
        .then(response => response.json())
        .then(data => {
            updateOpportunitiesTable(data);
        })
        .catch(error => {
            console.error('Error fetching opportunities:', error);
            showErrorMessage('Failed to load opportunities');
        })
        .finally(() => {
            if (button) {
                button.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Refresh';
                button.disabled = false;
            }
        });
}

// Update opportunities table
function updateOpportunitiesTable(opportunities) {
    const tbody = document.getElementById('opportunities-table');
    if (!tbody) return;
    
    if (opportunities.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">
                    <i class="fas fa-search me-2"></i>Raccolta opportunità in corso...
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = opportunities.map(opp => {
        const profitClass = opp.profit_percentage > 1.0 ? 'profit-high' : 'profit-positive';
        const timeAgo = getTimeAgo(new Date(opp.timestamp));
        
        return `
            <tr class="fade-in">
                <td>
                    <strong>${opp.symbol}</strong>
                </td>
                <td>
                    <span class="badge bg-primary">${opp.buy_exchange}</span>
                </td>
                <td>
                    <span class="badge bg-success">${opp.sell_exchange}</span>
                </td>
                <td class="currency">$${formatPrice(opp.buy_price)}</td>
                <td class="currency">$${formatPrice(opp.sell_price)}</td>
                <td class="${profitClass} percentage">
                    ${opp.profit_percentage.toFixed(3)}%
                    ${opp.profit_percentage > 1.0 ? '🔥' : ''}
                </td>
                <td class="currency text-success">$${opp.potential_profit.toFixed(2)}</td>
                <td class="text-muted">${timeAgo}</td>
            </tr>
        `;
    }).join('');
}

// Initialize charts
function initializeCharts() {
    const btcCtx = document.getElementById('btc-chart');
    const ethCtx = document.getElementById('eth-chart');
    
    if (btcCtx) {
        btcChart = createPriceChart(btcCtx, 'BTC/USDT');
        updatePriceChart(btcChart, 'BTC/USDT');
    }
    
    if (ethCtx) {
        ethChart = createPriceChart(ethCtx, 'ETH/USDT');
        updatePriceChart(ethChart, 'ETH/USDT');
    }
}

// Create price chart
function createPriceChart(ctx, symbol) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#f0f6fc'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#8b949e'
                    },
                    grid: {
                        color: '#30363d'
                    }
                },
                y: {
                    ticks: {
                        color: '#8b949e',
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: '#30363d'
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.4
                },
                point: {
                    radius: 2
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Update price charts
function updatePriceCharts() {
    if (btcChart) updatePriceChart(btcChart, 'BTC/USDT');
    if (ethChart) updatePriceChart(ethChart, 'ETH/USDT');
}

// Update individual price chart
function updatePriceChart(chart, symbol) {
    fetch(`/api/price-history/${encodeURIComponent(symbol)}`)
        .then(response => response.json())
        .then(data => {
            const exchanges = Object.keys(data);
            
            // If no data available yet, show a message
            if (exchanges.length === 0 || !data[exchanges[0]] || data[exchanges[0]].length === 0) {
                chart.data.labels = ['Waiting for data...'];
                chart.data.datasets = [{
                    label: 'No data available yet',
                    data: [0],
                    borderColor: '#6c757d',
                    backgroundColor: '#6c757d20'
                }];
                chart.update('none');
                return;
            }
            
            const colors = ['#0066cc', '#28a745', '#dc3545', '#ffc107', '#17a2b8'];
            
            chart.data.datasets = exchanges.map((exchange, index) => {
                const priceData = data[exchange].slice(-20); // Last 20 data points
                
                return {
                    label: exchange.toUpperCase(),
                    data: priceData.map(item => item.price),
                    borderColor: colors[index % colors.length],
                    backgroundColor: colors[index % colors.length] + '20',
                    fill: false,
                    pointBackgroundColor: colors[index % colors.length],
                    pointBorderColor: colors[index % colors.length],
                    tension: 0.1
                };
            });
            
            // Use timestamps from first exchange for labels
            if (exchanges.length > 0 && data[exchanges[0]].length > 0) {
                const firstExchange = data[exchanges[0]].slice(-20);
                chart.data.labels = firstExchange.map(item => {
                    const date = new Date(item.timestamp);
                    return date.toLocaleTimeString('en-US', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    });
                });
            }
            
            chart.update('none');
        })
        .catch(error => {
            console.warn(`Waiting for ${symbol} price data...`);
            // Show waiting message instead of error
            chart.data.labels = ['Collecting data...'];
            chart.data.datasets = [{
                label: 'Price data will appear soon',
                data: [0],
                borderColor: '#6c757d',
                backgroundColor: '#6c757d20'
            }];
            chart.update('none');
        });
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatPrice(price) {
    if (price >= 1000) {
        return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (price >= 1) {
        return price.toFixed(4);
    } else {
        return price.toFixed(6);
    }
}

function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins}m ago`;
    } else if (diffHours < 24) {
        return `${diffHours}h ago`;
    } else {
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }
}

function showErrorMessage(message) {
    console.error('Dashboard Error:', message);
    
    // Could add toast notifications here
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed top-0 end-0 m-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

// Export functions for global access
window.refreshOpportunities = refreshOpportunities;
window.refreshStats = refreshStats;
