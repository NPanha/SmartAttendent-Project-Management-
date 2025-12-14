// QR Generator specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize QR code scanner (if implemented)
    initializeQRScanner();
    
    // Setup form validation
    setupFormValidation();
    
    // Setup QR code animation
    setupQRAnimation();
});

function initializeQRScanner() {
    // This would initialize a QR scanner for teachers to scan student QR codes
    // For now, it's a placeholder for future enhancement
}

function setupFormValidation() {
    const form = document.querySelector('.qr-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const courseSelect = document.getElementById('course_id');
            const classSelect = document.getElementById('class_group');
            
            if (!courseSelect.value || !classSelect.value) {
                e.preventDefault();
                showNotification('Please select both course and class group', 'error');
                return false;
            }
            
            // Show loading state
            const submitBtn = form.querySelector('.generate-btn');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            submitBtn.disabled = true;
            
            // Re-enable after 3 seconds (in case of error)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 3000);
        });
    }
}

function setupQRAnimation() {
    const qrImages = document.querySelectorAll('.qr-image');
    qrImages.forEach(img => {
        img.addEventListener('load', function() {
            this.style.opacity = '0';
            this.style.transform = 'scale(0.8)';
            
            setTimeout(() => {
                this.style.transition = 'all 0.5s ease';
                this.style.opacity = '1';
                this.style.transform = 'scale(1)';
            }, 100);
        });
    });
}

function copyQRData() {
    const qrData = document.getElementById('qrData')?.value;
    if (qrData) {
        navigator.clipboard.writeText(qrData)
            .then(() => showNotification('QR data copied to clipboard!', 'success'))
            .catch(err => showNotification('Failed to copy QR data', 'error'));
    }
}

function showQRHistory() {
    // In a real app, this would show a modal with generated QR history
    showNotification('QR history feature coming soon!', 'info');
}