document.addEventListener('DOMContentLoaded', function() {
    const videoStream = document.getElementById('videoStream');
    const startCameraBtn = document.getElementById('startCamera');
    const stopCameraBtn = document.getElementById('stopCamera');
    const detectionStatus = document.getElementById('detectionStatus');
    const predictedLetter = document.getElementById('predictedLetter');
    const confidence = document.getElementById('confidence');
    const status = document.getElementById('status');
    const cameraStatus = document.getElementById('cameraStatus');
    const detectionMode = document.getElementById('detectionMode');
    const themeSwitcher = document.getElementById('themeSwitcher');

    let predictionInterval;
    let isCameraActive = false;

    // Theme Management
    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
    }

    function setTheme(theme) {
        // Add transition class for smooth theme switching
        document.body.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        themeSwitcher.textContent = theme === 'dark' ? '☀️' : '🌙';
        themeSwitcher.title = theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme';
        
        // Remove transition after animation completes
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    }

    // Initialize theme
    initTheme();

    // Theme switcher event listener
    themeSwitcher.addEventListener('click', toggleTheme);

    // Camera control handlers
    startCameraBtn.addEventListener('click', startCamera);
    stopCameraBtn.addEventListener('click', stopCamera);

    async function startCamera() {
        try {
            startCameraBtn.disabled = true;
            startCameraBtn.innerHTML = '<span class="loading"></span>Starting Camera...';
            detectionStatus.textContent = 'Initializing camera...';

            const response = await fetch('/start_camera');
            const result = await response.json();

            if (result.status === 'success') {
                isCameraActive = true;
                startCameraBtn.disabled = true;
                stopCameraBtn.disabled = false;
                startCameraBtn.innerHTML = '✅ Camera Active';
                stopCameraBtn.innerHTML = '⏹️ Stop Camera';
                detectionStatus.textContent = 'Camera active - Make hand gestures!';
                
                // Start video stream
                videoStream.src = '/video_feed';
                videoStream.style.display = 'block';
                
                // Update camera info
                cameraStatus.textContent = 'Active';
                detectionMode.textContent = 'Real-time detection running';
                
                // Add visual feedback
                document.querySelector('.video-container').classList.add('camera-active');
                
                // Start polling for predictions
                startPredictionPolling();
                
                showStatus('🎉 Camera started successfully! Ready for hand detection.', 'success');
            } else {
                showStatus('❌ Failed to start camera: ' + result.message, 'error');
                startCameraBtn.disabled = false;
                startCameraBtn.innerHTML = '📹 Start Camera';
            }
        } catch (error) {
            showStatus('🌐 Network error. Please check your connection.', 'error');
            startCameraBtn.disabled = false;
            startCameraBtn.innerHTML = '📹 Start Camera';
            console.error('Error starting camera:', error);
        }
    }

    async function stopCamera() {
        try {
            stopCameraBtn.disabled = true;
            stopCameraBtn.innerHTML = '<span class="loading"></span>Stopping Camera...';

            const response = await fetch('/stop_camera');
            const result = await response.json();

            if (result.status === 'success') {
                isCameraActive = false;
                startCameraBtn.disabled = false;
                stopCameraBtn.disabled = true;
                startCameraBtn.innerHTML = '📹 Start Camera';
                stopCameraBtn.innerHTML = '✅ Camera Stopped';
                detectionStatus.textContent = 'Camera stopped - Click Start Camera to begin';
                
                // Stop video stream
                videoStream.src = '';
                videoStream.style.display = 'none';
                
                // Update camera info
                cameraStatus.textContent = 'Stopped';
                detectionMode.textContent = 'Waiting for activation';
                
                // Remove visual feedback
                document.querySelector('.video-container').classList.remove('camera-active');
                
                // Stop polling for predictions
                stopPredictionPolling();
                
                showStatus('🛑 Camera stopped successfully!', 'success');
            } else {
                showStatus('❌ Failed to stop camera: ' + result.message, 'error');
                stopCameraBtn.disabled = false;
                stopCameraBtn.innerHTML = '⏹️ Stop Camera';
            }
        } catch (error) {
            showStatus('🌐 Network error. Please try again.', 'error');
            stopCameraBtn.disabled = false;
            stopCameraBtn.innerHTML = '⏹️ Stop Camera';
            console.error('Error stopping camera:', error);
        }
    }

    function startPredictionPolling() {
        // Clear any existing interval first
        if (predictionInterval) {
            clearInterval(predictionInterval);
            predictionInterval = null;
        }
        
        predictionInterval = setInterval(async () => {
            if (!isCameraActive) {
                clearInterval(predictionInterval);
                predictionInterval = null;
                return;
            }
            
            try {
                const response = await fetch('/get_prediction');
                const prediction = await response.json();
                
                updatePredictionDisplay(prediction);
            } catch (error) {
                console.error('Error fetching prediction:', error);
                // Stop polling on network errors
                clearInterval(predictionInterval);
                predictionInterval = null;
            }
        }, 100); // Update every 100ms for smooth real-time updates
    }

    function stopPredictionPolling() {
        if (predictionInterval) {
            clearInterval(predictionInterval);
            predictionInterval = null;
        }
        
        // Reset display
        predictedLetter.textContent = '?';
        confidence.textContent = '0%';
        status.textContent = 'Camera stopped';
        status.className = 'status';
    }

    function updatePredictionDisplay(prediction) {
        predictedLetter.textContent = prediction.letter;
        confidence.textContent = `${prediction.confidence}%`;
        
        if (prediction.status === 'success') {
            status.textContent = '🎯 Hand detected successfully!';
            status.className = 'status success';
        } else if (prediction.status === 'No hand detected') {
            status.textContent = '👋 No hand detected - Make a gesture!';
            status.className = 'status warning';
        } else {
            status.textContent = `⚠️ ${prediction.status}`;
            status.className = 'status error';
        }
    }

    function showStatus(message, type) {
        status.textContent = message;
        status.className = `status ${type}`;
    }

    // Handle video stream errors
    videoStream.addEventListener('error', function() {
        detectionStatus.textContent = 'Video stream error - Check camera permissions';
        showStatus('Video stream failed. Please check camera permissions.', 'error');
        // Reset button states on error
        startCameraBtn.disabled = false;
        startCameraBtn.innerHTML = '📹 Start Camera';
        stopCameraBtn.disabled = true;
        stopCameraBtn.innerHTML = '⏹️ Stop Camera';
        // Stop polling on error
        stopPredictionPolling();
        isCameraActive = false;
    });

    // Handle video stream load
    videoStream.addEventListener('load', function() {
        detectionStatus.textContent = 'Camera active - Make hand gestures!';
    });

    // Check server health on load
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            if (!data.model_loaded) {
                showStatus('❌ Model not loaded. Please restart the application.', 'error');
                detectionStatus.textContent = 'Model not available';
                startCameraBtn.disabled = true;
                startCameraBtn.innerHTML = '⚠️ Model Not Available';
            } else {
                showStatus('✅ System ready! Click Start Camera to begin real-time detection.', 'success');
                detectionStatus.textContent = 'Ready to start - Click Start Camera';
            }
        })
        .catch(error => {
            console.error('Health check failed:', error);
            showStatus('🌐 Server connection failed. Please check if the app is running.', 'error');
            detectionStatus.textContent = 'Connection error';
        });
});