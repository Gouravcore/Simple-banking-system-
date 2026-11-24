/**
 * KUBERA BANK – Dashboard JavaScript
 * Handles: Spending chart, analytics loading
 */

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // SPENDING ANALYTICS CHART
    // (Uses Chart.js and our /api/analytics endpoint)
    // ==========================================
    const chartCanvas = document.getElementById('spendingChart');

    if (chartCanvas && window.Chart) {
        // Fetch analytics data from the backend
        fetch('/api/analytics')
            .then(response => response.json())
            .then(data => {
                if (data.error || !data.months) {
                    // Show a placeholder chart if no data
                    renderPlaceholderChart(chartCanvas);
                    return;
                }
                renderSpendingChart(chartCanvas, data);
            })
            .catch(() => {
                renderPlaceholderChart(chartCanvas);
            });
    }

    function renderSpendingChart(canvas, data) {
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.months.length > 0 ? data.months : ['No Data'],
                datasets: [
                    {
                        label: 'Credits (₹)',
                        data: data.deposits.length > 0 ? data.deposits : [0],
                        backgroundColor: 'rgba(46, 125, 50, 0.7)',
                        borderColor: 'rgba(46, 125, 50, 1)',
                        borderWidth: 1,
                        borderRadius: 6,
                    },
                    {
                        label: 'Debits (₹)',
                        data: data.withdrawals.length > 0 ? data.withdrawals : [0],
                        backgroundColor: 'rgba(183, 28, 28, 0.6)',
                        borderColor: 'rgba(183, 28, 28, 1)',
                        borderWidth: 1,
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ₹${ctx.raw.toLocaleString('en-IN')}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: {
                            font: { size: 11 },
                            callback: (val) => '₹' + val.toLocaleString('en-IN')
                        }
                    }
                }
            }
        });
    }

    function renderPlaceholderChart(canvas) {
        // Show a demo chart when there is no transaction data yet
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [
                    {
                        label: 'Credits (₹)',
                        data: [0, 0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(46, 125, 50, 0.3)',
                        borderRadius: 6,
                    },
                    {
                        label: 'Debits (₹)',
                        data: [0, 0, 0, 0, 0, 0],
                        backgroundColor: 'rgba(183, 28, 28, 0.3)',
                        borderRadius: 6,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        grid: { color: 'rgba(0,0,0,0.05)' },
                        ticks: { callback: (val) => '₹' + val }
                    }
                }
            }
        });
    }


    // ==========================================
    // BALANCE NUMBER ANIMATION
    // (Counts up to the balance on page load)
    // ==========================================
    const balanceDisplay = document.getElementById('balanceDisplay');
    if (balanceDisplay) {
        const text    = balanceDisplay.textContent.trim();
        // Extract numeric value from "₹1,23,456.78"
        const numStr  = text.replace(/[₹,]/g, '');
        const target  = parseFloat(numStr);

        if (!isNaN(target) && target > 0) {
            let current  = 0;
            const steps  = 60;
            const increment = target / steps;

            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                }
                // Format as Indian currency
                balanceDisplay.textContent = '₹' + current.toLocaleString('en-IN', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }, 25);
        }
    }

});
