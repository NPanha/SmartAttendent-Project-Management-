// Main JavaScript for Smart Attendance System

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('-translate-x-full');
            if (overlay) {
                overlay.classList.toggle('hidden');
            }
            document.body.classList.toggle('overflow-hidden');
        });
        
        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.add('-translate-x-full');
                overlay.classList.add('hidden');
                document.body.classList.remove('overflow-hidden');
            });
        }
    }
    
    // Close mobile menu on clicking links
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 1024) {
                if (sidebar) sidebar.classList.add('-translate-x-full');
                if (overlay) overlay.classList.add('hidden');
                document.body.classList.remove('overflow-hidden');
            }
        });
    });
    
    // Flash message auto-close
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'all 0.3s ease';
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
    
    // Close result modal
    const closeResultBtn = document.getElementById('closeResult');
    const scanResultModal = document.getElementById('scanResultModal');
    
    if (closeResultBtn && scanResultModal) {
        closeResultBtn.addEventListener('click', () => {
            scanResultModal.classList.add('hidden');
        });
        
        // Close modal when clicking outside
        scanResultModal.addEventListener('click', (e) => {
            if (e.target === scanResultModal) {
                scanResultModal.classList.add('hidden');
            }
        });
    }
    
    // Scan again button
    const scanAgainBtn = document.getElementById('scanAgain');
    if (scanAgainBtn) {
        scanAgainBtn.addEventListener('click', () => {
            if (scanResultModal) scanResultModal.classList.add('hidden');
            // Restart scanner logic will be in qr-scanner.js
            if (typeof restartScanner === 'function') {
                restartScanner();
            }
        });
    }
    
    // Filter buttons
    const filterBtn = document.getElementById('filterBtn');
    if (filterBtn) {
        filterBtn.addEventListener('click', applyFilters);
    }
    
    // Chart period buttons
    const chartPeriodBtns = document.querySelectorAll('.chart-period-btn');
    chartPeriodBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            chartPeriodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const period = this.getAttribute('data-period');
            if (typeof updateChart === 'function') {
                updateChart(period);
            }
        });
    });
    
    // Day tabs for timetable
    const dayTabs = document.querySelectorAll('.day-tab');
    dayTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const day = this.getAttribute('data-day');
            
            // Update active tab
            dayTabs.forEach(t => {
                t.classList.remove('border-blue-500', 'text-blue-600', 'bg-blue-50');
                t.classList.add('border-transparent', 'text-gray-500');
            });
            this.classList.remove('border-transparent', 'text-gray-500');
            this.classList.add('border-blue-500', 'text-blue-600', 'bg-blue-50');
            
            // Show corresponding content
            document.querySelectorAll('.day-content').forEach(content => {
                content.classList.add('hidden');
            });
            const dayContent = document.getElementById(`day-${day.toLowerCase()}`);
            if (dayContent) {
                dayContent.classList.remove('hidden');
            }
        });
    });
    
    // Download timetable
    const downloadBtn = document.getElementById('downloadTimetable');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            showNotification('Timetable download feature will be implemented soon!', 'info');
        });
    }
    
    // Export data button
    const exportDataBtn = document.getElementById('exportDataBtn');
    if (exportDataBtn) {
        exportDataBtn.addEventListener('click', () => {
            showNotification('Data export feature will be implemented soon!', 'info');
        });
    }
    
    // Edit profile modal
    const editProfileBtn = document.getElementById('editProfileBtn');
    const editProfileModal = document.getElementById('editProfileModal');
    const closeEditModal = document.getElementById('closeEditModal');
    const cancelEdit = document.getElementById('cancelEdit');
    
    if (editProfileBtn && editProfileModal) {
        editProfileBtn.addEventListener('click', () => {
            editProfileModal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        });
        
        const closeModal = () => {
            editProfileModal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        };
        
        if (closeEditModal) closeEditModal.addEventListener('click', closeModal);
        if (cancelEdit) cancelEdit.addEventListener('click', closeModal);
        
        // Close modal when clicking outside
        editProfileModal.addEventListener('click', (e) => {
            if (e.target === editProfileModal) {
                closeModal();
            }
        });
    }
    
    // Change password form
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('currentPassword');
            const newPassword = document.getElementById('newPassword');
            const confirmPassword = document.getElementById('confirmPassword');
            
            if (!currentPassword || !newPassword || !confirmPassword) return;
            
            if (newPassword.value !== confirmPassword.value) {
                showNotification('New passwords do not match!', 'error');
                return;
            }
            
            if (newPassword.value.length < 6) {
                showNotification('Password must be at least 6 characters!', 'error');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Updating...';
                submitBtn.disabled = true;
                
                // Simulate API call
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    this.reset();
                    showNotification('Password changed successfully!', 'success');
                }, 1500);
            }
        });
    }
    
    // Initialize tooltips
    initTooltips();
});

function applyFilters() {
    // Get filter values
    const courseFilter = document.getElementById('courseFilter');
    const startDate = document.getElementById('startDate');
    const endDate = document.getElementById('endDate');
    
    if (!courseFilter || !startDate || !endDate) return;
    
    // Show loading state
    const filterBtn = document.getElementById('filterBtn');
    if (!filterBtn) return;
    
    const originalText = filterBtn.innerHTML;
    filterBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Applying...';
    filterBtn.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        console.log('Applying filters:', { 
            courseFilter: courseFilter.value, 
            startDate: startDate.value, 
            endDate: endDate.value 
        });
        
        // Reset button
        filterBtn.innerHTML = originalText;
        filterBtn.disabled = false;
        
        // Show success message
        showNotification('Filters applied successfully!', 'success');
    }, 1000);
}

function updateChart(period) {
    // This function would update the chart based on selected period
    console.log('Updating chart for period:', period);
    
    // In a real app, this would fetch new data and update the chart
    // For now, we'll just show a notification
    showNotification(`Showing ${period}ly attendance data`, 'info');
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.custom-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `custom-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform translate-x-full ${getNotificationClass(type)}`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="${getNotificationIcon(type)} mr-3"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
        notification.classList.add('translate-x-0');
    }, 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('translate-x-0');
        notification.classList.add('translate-x-full');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function getNotificationClass(type) {
    switch(type) {
        case 'success': return 'bg-green-100 text-green-800 border border-green-200';
        case 'error': return 'bg-red-100 text-red-800 border border-red-200';
        case 'warning': return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
        default: return 'bg-blue-100 text-blue-800 border border-blue-200';
    }
}

function getNotificationIcon(type) {
    switch(type) {
        case 'success': return 'fas fa-check-circle text-green-600';
        case 'error': return 'fas fa-exclamation-circle text-red-600';
        case 'warning': return 'fas fa-exclamation-triangle text-yellow-600';
        default: return 'fas fa-info-circle text-blue-600';
    }
}

function initTooltips() {
    // Initialize tooltips for elements with data-tooltip attribute
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'fixed z-50 px-3 py-2 text-sm text-white bg-gray-900 rounded-lg shadow-lg whitespace-nowrap';
            tooltip.textContent = e.target.dataset.tooltip;
            
            document.body.appendChild(tooltip);
            
            const rect = e.target.getBoundingClientRect();
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            tooltip.style.top = `${rect.top + scrollTop - tooltip.offsetHeight - 10}px`;
            tooltip.style.left = `${rect.left + (rect.width - tooltip.offsetWidth) / 2}px`;
            
            e.target._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', (e) => {
            if (e.target._tooltip) {
                e.target._tooltip.remove();
                delete e.target._tooltip;
            }
        });
    });
}

// Utility function to format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Utility function to format time
function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Global function to toggle password visibility
window.togglePassword = function(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const button = input.nextElementSibling;
    if (!button) return;
    
    const icon = button.querySelector('i');
    if (!icon) return;
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
};