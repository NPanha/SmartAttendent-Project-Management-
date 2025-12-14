// Reports page specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize chart resizing
    initializeChartResizing();
    
    // Setup report filtering
    setupReportFiltering();
});

function initializeDatePickers() {
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    
    if (startDate && endDate) {
        // Set default dates (last 30 days)
        const today = new Date();
        const thirtyDaysAgo = new Date(today);
        thirtyDaysAgo.setDate(today.getDate() - 30);
        
        startDate.value = thirtyDaysAgo.toISOString().split('T')[0];
        endDate.value = today.toISOString().split('T')[0];
        
        // Set max date to today
        startDate.max = today.toISOString().split('T')[0];
        endDate.max = today.toISOString().split('T')[0];
        
        // Ensure end date is not before start date
        startDate.addEventListener('change', function() {
            endDate.min = this.value;
        });
        
        endDate.addEventListener('change', function() {
            startDate.max = this.value;
        });
    }
}

function initializeChartResizing() {
    // Resize charts on window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            const charts = [attendanceChart, trendChart];
            charts.forEach(chart => {
                if (chart) chart.resize();
            });
        }, 250);
    });
}

function setupReportFiltering() {
    const filterTabs = document.querySelectorAll('.filter-tab');
    const periodFilter = document.getElementById('periodFilter');
    
    if (periodFilter) {
        periodFilter.addEventListener('change', function() {
            applyReportFilters();
        });
    }
}

function applyReportFilters() {
    const period = document.getElementById('periodFilter')?.value || 'daily';
    const startDate = document.getElementById('startDate')?.value;
    const endDate = document.getElementById('endDate')?.value;
    
    // Show loading state
    showNotification('Loading report data...', 'info');
    
    // In a real app, fetch filtered data
    setTimeout(() => {
        showNotification('Report data loaded', 'success');
    }, 1000);
}

function generatePDFReport() {
    showNotification('Generating PDF report...', 'info');
    
    // In a real app, make API call to generate PDF
    setTimeout(() => {
        const link = document.createElement('a');
        link.href = '/api/generate-pdf-report';
        link.download = 'attendance_report.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('PDF report downloaded', 'success');
    }, 2000);
}

function shareReport() {
    if (navigator.share) {
        navigator.share({
            title: 'Attendance Report',
            text: 'Check out this attendance report',
            url: window.location.href
        })
        .then(() => showNotification('Report shared successfully', 'success'))
        .catch(error => showNotification('Error sharing report', 'error'));
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href)
            .then(() => showNotification('Report link copied to clipboard', 'success'))
            .catch(() => showNotification('Unable to share report', 'error'));
    }
}