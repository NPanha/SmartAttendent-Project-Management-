// Face Recognition functionality
document.addEventListener('DOMContentLoaded', function() {
    let video = document.getElementById('video');
    let canvas = document.getElementById('canvas');
    let context = canvas.getContext('2d');
    let isCameraOn = false;
    let faceDetectionInterval;
    let currentStream;
    
    // Elements
    const startCameraBtn = document.getElementById('startCamera');
    const stopCameraBtn = document.getElementById('stopCamera');
    const captureFaceBtn = document.getElementById('captureFace');
    const enrollFaceBtn = document.getElementById('enrollFace');
    const detectionCountEl = document.getElementById('detectionCount');
    const confidenceLevelEl = document.getElementById('confidenceLevel');
    const identityStatusEl = document.getElementById('identityStatus');
    const attendanceStatusEl = document.getElementById('attendanceStatus');
    const faceOverlay = document.getElementById('faceOverlay');
    
    // Initialize - hide overlay initially
    if (faceOverlay) {
        faceOverlay.style.display = 'none';
    }
    
    initializeFaceRecognition();
    
    function initializeFaceRecognition() {
        // Check for camera support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showNotification('Camera not supported on this device', 'error');
            disableAllControls();
            return;
        }
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        if (startCameraBtn) {
            startCameraBtn.addEventListener('click', startCamera);
        }
        
        if (stopCameraBtn) {
            stopCameraBtn.addEventListener('click', stopCamera);
        }
        
        if (captureFaceBtn) {
            captureFaceBtn.addEventListener('click', captureAndVerifyFace);
        }
        
        if (enrollFaceBtn) {
            enrollFaceBtn.addEventListener('click', startFaceEnrollment);
        }
        
        // Modal close buttons
        const closeFaceResult = document.getElementById('closeFaceResult');
        if (closeFaceResult) {
            closeFaceResult.addEventListener('click', () => {
                document.getElementById('faceResultModal').classList.add('hidden');
            });
        }
        
        const tryAgainBtn = document.getElementById('tryAgain');
        if (tryAgainBtn) {
            tryAgainBtn.addEventListener('click', () => {
                document.getElementById('faceResultModal').classList.add('hidden');
                if (isCameraOn) {
                    setTimeout(startFaceDetection, 1000);
                }
            });
        }
        
        const closeEnrollmentModal = document.getElementById('closeEnrollmentModal');
        if (closeEnrollmentModal) {
            closeEnrollmentModal.addEventListener('click', () => {
                document.getElementById('enrollmentModal').classList.add('hidden');
            });
        }
        
        const cancelEnrollment = document.getElementById('cancelEnrollment');
        if (cancelEnrollment) {
            cancelEnrollment.addEventListener('click', () => {
                document.getElementById('enrollmentModal').classList.add('hidden');
            });
        }
        
        const startEnrollmentBtn = document.getElementById('startEnrollment');
        if (startEnrollmentBtn) {
            startEnrollmentBtn.addEventListener('click', beginEnrollmentProcess);
        }
    }
    
    async function startCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            };
            
            currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = currentStream;
            isCameraOn = true;
            
            // Show the face overlay when camera starts
            if (faceOverlay) {
                faceOverlay.style.display = 'block';
            }
            
            // Update UI
            updateCameraControls();
            showNotification('Camera started successfully', 'success');
            
            // Start face detection
            setTimeout(startFaceDetection, 500);
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            showNotification('Failed to access camera. Please check permissions.', 'error');
        }
    }
    
    function stopCamera() {
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
            currentStream = null;
        }
        
        if (video.srcObject) {
            video.srcObject = null;
        }
        
        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
            faceDetectionInterval = null;
        }
        
        // Hide the face overlay when camera stops
        if (faceOverlay) {
            faceOverlay.style.display = 'none';
        }
        
        isCameraOn = false;
        updateCameraControls();
        resetDetectionUI();
        showNotification('Camera stopped', 'info');
    }
    
    function updateCameraControls() {
        if (startCameraBtn) startCameraBtn.disabled = isCameraOn;
        if (stopCameraBtn) stopCameraBtn.disabled = !isCameraOn;
        if (captureFaceBtn) captureFaceBtn.disabled = !isCameraOn;
        
        // Update button text based on camera state
        if (startCameraBtn) {
            if (isCameraOn) {
                startCameraBtn.innerHTML = '<i class="fas fa-video"></i><span>Camera Running</span>';
                startCameraBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
                startCameraBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
            } else {
                startCameraBtn.innerHTML = '<i class="fas fa-video"></i><span>Start Camera</span>';
                startCameraBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                startCameraBtn.classList.add('bg-green-600', 'hover:bg-green-700');
            }
        }
    }
    
    function resetDetectionUI() {
        detectionCountEl.textContent = '0';
        confidenceLevelEl.textContent = '0%';
        identityStatusEl.textContent = 'Camera Off';
        identityStatusEl.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800';
    }
    
    async function detectFace() {
        if (!isCameraOn) return;
        
        try {
            // Set canvas dimensions to match video
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Draw current video frame to canvas
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert canvas to base64 image
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to server for face detection
            const response = await fetch('/api/capture-face', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageData
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                detectionCountEl.textContent = result.face_count;
                confidenceLevelEl.textContent = result.confidence + '%';
                
                if (result.face_detected) {
                    if (result.confidence > 60) {
                        identityStatusEl.textContent = 'Face Detected';
                        identityStatusEl.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800';
                    } else {
                        identityStatusEl.textContent = 'Face Too Small';
                        identityStatusEl.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800';
                    }
                } else {
                    identityStatusEl.textContent = 'No Face Detected';
                    identityStatusEl.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800';
                }
            }
        } catch (error) {
            console.error('Face detection error:', error);
        }
    }
    
    function startFaceDetection() {
        if (!isCameraOn || faceDetectionInterval) return;
        
        // Update status
        identityStatusEl.textContent = 'Detecting...';
        identityStatusEl.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800';
        
        // Start face detection loop
        faceDetectionInterval = setInterval(() => {
            if (!isCameraOn) {
                clearInterval(faceDetectionInterval);
                return;
            }
            
            detectFace();
        }, 1500); // Check every 1.5 seconds
    }
    
    async function captureAndVerifyFace() {
        if (!isCameraOn) {
            showNotification('Please start camera first', 'warning');
            return;
        }
        
        // Show loading
        const modal = document.getElementById('faceResultModal');
        const resultIcon = document.getElementById('faceResultIcon');
        const resultTitle = document.getElementById('faceResultTitle');
        const resultMessage = document.getElementById('faceResultMessage');
        
        resultIcon.innerHTML = '<div class="spinner mx-auto"></div>';
        resultTitle.textContent = 'Verifying Face...';
        resultMessage.textContent = 'Please wait while we verify your identity';
        modal.classList.remove('hidden');
        
        // Stop face detection temporarily
        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
            faceDetectionInterval = null;
        }
        
        try {
            // Capture current frame
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg', 0.9);
            
            // Send to server for verification
            const response = await fetch('/api/mark-face-attendance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageData,
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showFaceResult('success', 'Attendance Marked!', data.message);
                attendanceStatusEl.textContent = 'Marked';
                attendanceStatusEl.className = 'px-3 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800';
                
                // Update confidence with actual value from server
                if (data.confidence) {
                    confidenceLevelEl.textContent = Math.round(data.confidence) + '%';
                }
            } else {
                showFaceResult('error', 'Verification Failed', data.message);
            }
        } catch (error) {
            console.error('Verification error:', error);
            showFaceResult('error', 'Network Error', 'Please check your connection and try again.');
        }
        
        // Restart face detection
        setTimeout(() => {
            if (isCameraOn) {
                startFaceDetection();
            }
        }, 2000);
    }
    
    function markAttendanceWithFace() {
        // Old function kept for backward compatibility
        captureAndVerifyFace();
    }
    
    function showFaceResult(type, title, message) {
        const resultIcon = document.getElementById('faceResultIcon');
        const resultTitle = document.getElementById('faceResultTitle');
        const resultMessage = document.getElementById('faceResultMessage');
        
        if (type === 'success') {
            resultIcon.innerHTML = '<div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto"><i class="fas fa-check text-4xl text-green-600"></i></div>';
            resultTitle.textContent = title;
            resultTitle.className = 'text-xl font-bold text-center mb-2 text-green-600';
            resultMessage.textContent = message;
        } else {
            resultIcon.innerHTML = '<div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto"><i class="fas fa-times text-4xl text-red-600"></i></div>';
            resultTitle.textContent = title;
            resultTitle.className = 'text-xl font-bold text-center mb-2 text-red-600';
            resultMessage.textContent = message;
        }
    }
    
    function startFaceEnrollment() {
        document.getElementById('enrollmentModal').classList.remove('hidden');
    }
    
    function beginEnrollmentProcess() {
        const modal = document.getElementById('enrollmentModal');
        const startEnrollmentBtn = document.getElementById('startEnrollment');
        
        // Change button to show progress
        startEnrollmentBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Enrolling...';
        startEnrollmentBtn.disabled = true;
        
        // For now, simulate enrollment
        setTimeout(() => {
            modal.classList.add('hidden');
            showNotification('Face enrollment feature coming soon!', 'info');
            
            // Reset button
            startEnrollmentBtn.innerHTML = 'Start Enrollment';
            startEnrollmentBtn.disabled = false;
        }, 2000);
    }
    
    function disableAllControls() {
        if (startCameraBtn) startCameraBtn.disabled = true;
        if (stopCameraBtn) stopCameraBtn.disabled = true;
        if (captureFaceBtn) captureFaceBtn.disabled = true;
        if (enrollFaceBtn) enrollFaceBtn.disabled = true;
    }
    
    function showNotification(message, type = 'info') {
        // Simple notification function
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // Initialize with camera off state
    resetDetectionUI();
    updateCameraControls();
    
    // Clean up
    window.addEventListener('beforeunload', () => {
        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
        }
        if (currentStream) {
            currentStream.getTracks().forEach(track => track.stop());
        }
    });
});