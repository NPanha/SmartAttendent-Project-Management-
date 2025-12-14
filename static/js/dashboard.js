// Dashboard specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
    
    // Initialize animations
    animateStats();
    
    // Initialize auto-refresh for today's classes
    setInterval(updateTodaySchedule, 60000); // Update every minute
});

function showTooltip(event) {
    const tooltip = event.target.getAttribute('data-tooltip');
    if (!tooltip) return;
    
    const tooltipEl = document.createElement('div');
    tooltipEl.className = 'tooltip';
    tooltipEl.textContent = tooltip;
    document.body.appendChild(tooltipEl);
    
    const rect = event.target.getBoundingClientRect();
    tooltipEl.style.top = rect.top - tooltipEl.offsetHeight - 10 + 'px';
    tooltipEl.style.left = rect.left + (rect.width - tooltipEl.offsetWidth) / 2 + 'px';
}

function hideTooltip(event) {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function animateStats() {
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(stat => {
        const value = parseInt(stat.textContent);
        if (!isNaN(value)) {
            animateCounter(stat, 0, value, 2000);
        }
    });
}

function animateCounter(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);
        element.textContent = current + (element.textContent.includes('%') ? '%' : '');
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function updateTodaySchedule() {
    // In a real app, fetch updated schedule data
    console.log('Updating today\'s schedule...');
}