// Profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Edit Profile Modal
    const editProfileBtn = document.getElementById('editProfileBtn');
    const editProfileModal = document.getElementById('editProfileModal');
    const closeEditModal = document.getElementById('closeEditModal');
    const cancelEdit = document.getElementById('cancelEdit');
    const editProfileForm = document.getElementById('editProfileForm');
    
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
        
        // Handle form submission
        if (editProfileForm) {
            editProfileForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                // Get form data
                const formData = new FormData(this);
                const data = Object.fromEntries(formData);
                
                // Show loading state
                const submitBtn = this.querySelector('button[type="submit"]');
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Saving...';
                submitBtn.disabled = true;
                
                // Simulate API call
                setTimeout(() => {
                    console.log('Updating profile with:', data);
                    
                    // Reset button
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                    
                    // Close modal
                    closeModal();
                    
                    // Show success message
                    showNotification('Profile updated successfully!', 'success');
                    
                    // Update displayed data (in real app, this would be a page reload or DOM update)
                    updateProfileDisplay(data);
                }, 1500);
            });
        }
    }
    
    // Change Password Form
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            // Validation
            if (newPassword !== confirmPassword) {
                showNotification('New passwords do not match', 'error');
                return;
            }
            
            if (newPassword.length < 6) {
                showNotification('Password must be at least 6 characters', 'error');
                return;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Updating...';
            submitBtn.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                console.log('Changing password...');
                
                // Reset button and form
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                this.reset();
                
                // Show success message
                showNotification('Password changed successfully!', 'success');
            }, 1500);
        });
    }
    
    // Toggle password visibility
    window.togglePassword = function(inputId) {
        const input = document.getElementById(inputId);
        const icon = input.nextElementSibling.querySelector('i');
        
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
    
    // Profile picture upload simulation
    const profilePicBtn = document.querySelector('.profile-pic-upload-btn');
    if (profilePicBtn) {
        profilePicBtn.addEventListener('click', () => {
            // In real app, this would trigger file input
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            
            fileInput.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    // Simulate upload
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        // In real app, upload to server
                        console.log('Profile picture uploaded');
                        showNotification('Profile picture updated successfully!', 'success');
                        
                        // Update preview (would be done via server response)
                        const profilePic = document.querySelector('.profile-pic');
                        if (profilePic) {
                            profilePic.style.backgroundImage = `url(${e.target.result})`;
                            profilePic.innerHTML = '';
                        }
                    };
                    reader.readAsDataURL(file);
                }
            };
            
            fileInput.click();
        });
    }
});

function updateProfileDisplay(data) {
    // Update displayed profile information
    // In a real app, this would update the DOM elements with new data
    // For now, we'll just log it
    console.log('Profile data to display:', data);
}

function showNotification(message, type = 'info') {
    // Use the same notification function from main.js
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        // Fallback alert
        alert(message);
    }
}