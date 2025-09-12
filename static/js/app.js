document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const imageInput = document.getElementById('imageInput');
    const previewSection = document.getElementById('previewSection');
    const previewImage = document.getElementById('previewImage');
    const predictBtn = document.getElementById('predictBtn');
    const resultSection = document.getElementById('resultSection');
    const predictedLetter = document.getElementById('predictedLetter');
    const confidence = document.getElementById('confidence');
    const status = document.getElementById('status');
    const resetBtn = document.getElementById('resetBtn');

    // Upload area click handler
    uploadArea.addEventListener('click', () => {
        imageInput.click();
    });

    // File input change handler
    imageInput.addEventListener('change', handleFileSelect);

    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    // Predict button handler
    predictBtn.addEventListener('click', predictImage);

    // Reset button handler
    resetBtn.addEventListener('click', resetForm);

    function handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            handleFile(file);
        }
    }

    function handleFile(file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
            showError('Please select a valid image file.');
            return;
        }

        // Validate file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showError('Image size should be less than 5MB.');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewSection.style.display = 'block';
            resultSection.style.display = 'none';
        };
        reader.readAsDataURL(file);
    }

    async function predictImage() {
        const imageData = previewImage.src;
        if (!imageData) {
            showError('Please select an image first.');
            return;
        }

        // Show loading state
        predictBtn.disabled = true;
        predictBtn.innerHTML = '<span class="loading"></span>Predicting...';

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData })
            });

            const result = await response.json();

            if (result.status === 'success') {
                showResult(result.prediction, result.confidence);
            } else {
                showError(result.error || 'Failed to process image.');
            }
        } catch (error) {
            showError('Network error. Please try again.');
            console.error('Error:', error);
        } finally {
            // Reset button state
            predictBtn.disabled = false;
            predictBtn.innerHTML = '🔍 Predict Letter';
        }
    }

    function showResult(letter, conf) {
        predictedLetter.textContent = letter;
        confidence.textContent = `Confidence: ${conf}%`;
        status.textContent = 'Prediction successful!';
        status.className = 'status success';
        
        resultSection.style.display = 'block';
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }

    function showError(message) {
        status.textContent = message;
        status.className = 'status error';
        resultSection.style.display = 'block';
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }

    function resetForm() {
        previewSection.style.display = 'none';
        resultSection.style.display = 'none';
        imageInput.value = '';
        uploadArea.classList.remove('dragover');
    }

    // Check server health on load
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            if (!data.model_loaded) {
                showError('Model not loaded. Please try again later.');
            }
        })
        .catch(error => {
            console.error('Health check failed:', error);
        });
});
