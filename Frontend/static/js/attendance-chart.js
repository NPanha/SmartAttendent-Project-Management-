// Attendance Chart using Chart.js
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('attendanceChart');
    
    if (!ctx) return;
    
    let attendanceChart;
    
    function initializeChart(period = 'week') {
        if (attendanceChart) {
            attendanceChart.destroy();
        }
        
        const { labels, data, colors } = getChartData(period);
        
        attendanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Attendance Rate',
                    data: data,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: function(context) {
                        const index = context.dataIndex;
                        return colors[index] || '#667eea';
                    },
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        padding: 12,
                        cornerRadius: 6,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `Attendance: ${context.parsed.y}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            },
                            color: '#6b7280'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#6b7280'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    function getChartData(period) {
        // Mock data - in real app, this would come from API
        switch(period) {
            case 'week':
                return {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    data: [85, 92, 78, 95, 88, 100, 0],
                    colors: ['#10b981', '#10b981', '#f59e0b', '#10b981', '#10b981', '#10b981', '#6b7280']
                };
            case 'month':
                return {
                    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                    data: [88, 92, 85, 90],
                    colors: ['#10b981', '#10b981', '#10b981', '#10b981']
                };
            case 'year':
                return {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    data: [85, 88, 90, 92, 87, 89, 91, 93, 90, 92, 94, 96],
                    colors: Array(12).fill('#10b981')
                };
            default:
                return {
                    labels: [],
                    data: [],
                    colors: []
                };
        }
    }
    
    // Initialize with week data
    initializeChart('week');
    
    // Update chart when period buttons are clicked
    const periodButtons = document.querySelectorAll('[data-period]');
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            const period = this.getAttribute('data-period');
            initializeChart(period);
        });
    });
});