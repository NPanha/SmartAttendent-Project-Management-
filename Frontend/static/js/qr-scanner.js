// QR Scanner functionality with camera control
document.addEventListener('DOMContentLoaded', function() {
    let html5QrCode;
    let currentCameraId;
    let isCameraOn = false;
    let cameras = [];
    
    const qrReader = document.getElementById('qr-reader');
    const toggleCameraBtn = document.getElementById('toggleCamera');
    const uploadQrBtn = document.getElementById('uploadQr');
    const cameraToggleBtn = document.getElementById('cameraToggle');
    
    function initializeScanner() {
        if (!qrReader) return;
        
        html5QrCode = new Html5Qrcode("qr-reader");
        
        // Get available cameras
        Html5Qrcode.getCameras().then(availableCameras => {
            if (availableCameras && availableCameras.length) {
                cameras = availableCameras;
                // Use back camera if available, otherwise use first camera
                const backCamera = cameras.find(c => c.label.toLowerCase().includes('back'));
                currentCameraId = backCamera ? backCamera.id : cameras[0].id;
                
                // Show camera controls
                updateCameraControls();
                
                // Auto-start camera (optional)
                // startCamera();
            } else {
                showNoCameraError();
            }
        }).catch(err => {
            console.error("Error getting cameras:", err);
            showNoCameraError();
        });
    }
    
    function startCamera() {
        if (!html5QrCode || !currentCameraId) return;
        
        const qrCodeSuccessCallback = (decodedText, decodedResult) => {
            handleQRScan(decodedText);
        };
        
        const config = { 
            fps: 10,
            qrbox: { width: 250, height: 250 },
            aspectRatio: 1.0,
            experimentalFeatures: {
                useBarCodeDetectorIfSupported: true
            }
        };
        
        html5QrCode.start(
            currentCameraId,
            config,
            qrCodeSuccessCallback,
            (errorMessage) => {
                // QR code parsing error, ignore it
                console.debug("QR scanning error:", errorMessage);
            }
        ).then(() => {
            isCameraOn = true;
            updateCameraButton();
            showNotification('Camera started successfully', 'success');
        }).catch(err => {
            console.error("Error starting camera:", err);
            showNotification('Failed to start camera. Please check permissions.', 'error');
        });
    }
    
    function stopCamera() {
        if (!html5QrCode || !isCameraOn) return;
        
        html5QrCode.stop().then(() => {
            isCameraOn = false;
            updateCameraButton();
            showNotification('Camera stopped', 'info');
        }).catch(err => {
            console.error("Error stopping camera:", err);
        });
    }
    
    function toggleCamera() {
        if (isCameraOn) {
            stopCamera();
        } else {
            startCamera();
        }
    }
    
    function switchCamera() {
        if (!html5QrCode || cameras.length < 2) {
            showNotification('Only one camera available', 'warning');
            return;
        }
        
        if (isCameraOn) {
            html5QrCode.stop().then(() => {
                const currentIndex = cameras.findIndex(c => c.id === currentCameraId);
                const nextIndex = (currentIndex + 1) % cameras.length;
                currentCameraId = cameras[nextIndex].id;
                
                showNotification(`Switched to ${cameras[nextIndex].label}`, 'info');
                startCamera();
            }).catch(err => {
                console.error("Error stopping camera:", err);
            });
        } else {
            const currentIndex = cameras.findIndex(c => c.id === currentCameraId);
            const nextIndex = (currentIndex + 1) % cameras.length;
            currentCameraId = cameras[nextIndex].id;
            updateCameraControls();
            showNotification(`Selected ${cameras[nextIndex].label}`, 'info');
        }
    }
    
    function updateCameraButton() {
        if (!cameraToggleBtn) return;
        
        const icon = cameraToggleBtn.querySelector('i');
        const text = cameraToggleBtn.querySelector('span');
        
        if (isCameraOn) {
            cameraToggleBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
            cameraToggleBtn.classList.add('bg-red-600', 'hover:bg-red-700');
            icon.className = 'fas fa-video-slash';
            text.textContent = 'Stop Camera';
        } else {
            cameraToggleBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
            cameraToggleBtn.classList.add('bg-green-600', 'hover:bg-green-700');
            icon.className = 'fas fa-video';
            text.textContent = 'Start Camera';
        }
    }
    
    function updateCameraControls() {
        if (!toggleCameraBtn) return;
        
        if (cameras.length > 1) {
            toggleCameraBtn.style.display = 'flex';
            const cameraLabel = cameras.find(c => c.id === currentCameraId)?.label || 'Camera';
            toggleCameraBtn.querySelector('span').textContent = `Switch Camera (${cameras.length} available)`;
        } else {
            toggleCameraBtn.style.display = 'none';
        }
    }
    
    function handleQRScan(qrData) {
        console.log('QR Code scanned:', qrData);
        console.log('Type of qrData:', typeof qrData);
        
        // Extract the actual QR text from the scanner result
        let qrText;
        if (typeof qrData === 'object' && qrData !== null) {
            // Check if it's the html5-qrcode format with decodedText
            if (qrData.decodedText) {
                qrText = qrData.decodedText;
                console.log('Found decodedText:', qrText);
            } else {
                // Try to stringify and parse
                qrText = JSON.stringify(qrData);
            }
        } else if (typeof qrData === 'string') {
            qrText = qrData;
        } else {
            showFaceResult('error', 'Invalid QR Code', 'Unsupported QR code format');
            return;
        }
        
        // Now parse the JSON string
        let parsedData;
        try {
            parsedData = JSON.parse(qrText);
            console.log('Successfully parsed QR data:', parsedData);
        } catch (e) {
            console.error('Failed to parse QR as JSON:', e);
            console.error('QR text that failed:', qrText);
            showFaceResult('error', 'Invalid QR Code', 'QR code data is not valid JSON');
            return;
        }
        
        // Validate the parsed data
        if (!parsedData.course_code || !parsedData.class_group) {
            console.error('Missing required fields in QR data:', parsedData);
            console.error('Available fields:', Object.keys(parsedData));
            showFaceResult('error', 'Invalid QR Code', 'QR code missing required information');
            return;
        }
        
        console.log('Parsed QR Data:', parsedData);
        console.log('Current time:', new Date().toISOString());
        
        // Stop camera temporarily
        if (isCameraOn) {
            html5QrCode.pause();
        }
        
        // Show loading state
        const resultIcon = document.getElementById('resultIcon');
        const resultTitle = document.getElementById('resultTitle');
        const resultMessage = document.getElementById('resultMessage');
        const modal = document.getElementById('scanResultModal');
        
        resultIcon.innerHTML = '<div class="spinner mx-auto"></div>';
        resultTitle.textContent = 'Processing...';
        resultMessage.textContent = 'Verifying attendance data';
        modal.classList.remove('hidden');
        
        // Verify QR and mark attendance
        verifyQRCode(parsedData);
    }
    
    function verifyQRCode(qrData) {
        // Convert object back to JSON string for API call
        const qrDataString = JSON.stringify(qrData);
        
        // Send to API
        fetch('/api/mark-attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                qrData: qrDataString,  // Send as string
                timestamp: new Date().toISOString(),
                studentId: '{{ session.get("student_id") }}'  // Add student ID if available
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.message || 'Server error');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showScanResult('success', 'Attendance Marked!', data.message);
            } else {
                showScanResult('error', 'Failed!', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showScanResult('error', 'Error', error.message || 'Failed to mark attendance. Please try again.');
        });
    }
    
    function showScanResult(type, title, message) {
        const resultIcon = document.getElementById('resultIcon');
        const resultTitle = document.getElementById('resultTitle');
        const resultMessage = document.getElementById('resultMessage');
        
        if (type === 'success') {
            resultIcon.innerHTML = '<div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto"><i class="fas fa-check text-4xl text-green-600"></i></div>';
            resultTitle.textContent = title;
            resultTitle.className = 'text-xl font-bold text-center mb-2 text-green-600';
            resultMessage.textContent = message;
            
            // Restart camera after 3 seconds
            setTimeout(() => {
                document.getElementById('scanResultModal').classList.add('hidden');
                if (isCameraOn) {
                    html5QrCode.resume();
                }
            }, 3000);
        } else {
            resultIcon.innerHTML = '<div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto"><i class="fas fa-times text-4xl text-red-600"></i></div>';
            resultTitle.textContent = title;
            resultTitle.className = 'text-xl font-bold text-center mb-2 text-red-600';
            resultMessage.textContent = message;
            
            // Allow retry
            document.getElementById('scanAgain').onclick = () => {
                document.getElementById('scanResultModal').classList.add('hidden');
                if (isCameraOn) {
                    html5QrCode.resume();
                }
            };
        }
    }
    
    function showNoCameraError() {
        if (!qrReader) return;
        
        qrReader.innerHTML = `
            <div class="text-center p-8">
                <i class="fas fa-video-slash text-4xl text-gray-300 mb-4"></i>
                <h3 class="text-lg font-semibold text-gray-700 mb-2">Camera Not Available</h3>
                <p class="text-gray-500 mb-4">Please allow camera access or use a device with a camera.</p>
                <button onclick="location.reload()" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">
                    Try Again
                </button>
            </div>
        `;
        
        if (cameraToggleBtn) cameraToggleBtn.style.display = 'none';
        if (toggleCameraBtn) toggleCameraBtn.style.display = 'none';
    }
    
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            // Try to read QR from image
            const img = new Image();
            img.onload = function() {
                // Use html5-qrcode to scan from image
                if (html5QrCode) {
                    html5QrCode.scanFileV2(file, true)
                        .then(decodedText => {
                            handleQRScan(decodedText);
                        })
                        .catch(err => {
                            showNotification('No QR code found in image', 'error');
                        });
                }
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
    
    // Initialize QR scanner
    if (qrReader) {
        initializeScanner();
    }
    
    // Event listeners
    if (cameraToggleBtn) {
        cameraToggleBtn.addEventListener('click', toggleCamera);
    }
    
    if (toggleCameraBtn) {
        toggleCameraBtn.addEventListener('click', switchCamera);
    }
    
    if (uploadQrBtn) {
        uploadQrBtn.addEventListener('click', () => {
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = 'image/*';
            fileInput.onchange = handleFileUpload;
            fileInput.click();
        });
    }
    
    // Clean up on page leave
    window.addEventListener('beforeunload', () => {
        if (html5QrCode && isCameraOn) {
            html5QrCode.stop().catch(err => console.error("Error stopping scanner:", err));
        }
    });
});