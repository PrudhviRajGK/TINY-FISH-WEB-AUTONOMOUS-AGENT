// Configuration
const API_BASE_URL = window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/api/v1/videos`;

// DOM Elements
const form = document.getElementById('videoForm');
const generateBtn = document.getElementById('generateBtn');
const statusDiv = document.getElementById('status');
const statusMessage = document.getElementById('statusMessage');
const spinner = document.getElementById('spinner');
const resultDiv = document.getElementById('result');
const videoList = document.getElementById('videoList');

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const topic = document.getElementById('topic').value.trim();
    const duration = parseInt(document.getElementById('duration').value);
    const keyPointsText = document.getElementById('keyPoints').value.trim();
    
    // Parse key points
    const keyPoints = keyPointsText
        ? keyPointsText.split('\n').filter(point => point.trim())
        : [];
    
    // Prepare request
    const requestData = {
        topic,
        duration,
        key_points: keyPoints.length > 0 ? keyPoints : [],
        style: 'educational'
    };
    
    // Show loading state
    showStatus('Generating video... This may take 5-10 minutes.', true);
    generateBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_ENDPOINT}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showStatus('Video generation started successfully!', false, 'success');
            
            // Show the video in results
            setTimeout(() => {
                loadVideos();
            }, 1000);
            
            // Reset form
            form.reset();
        } else {
            showStatus(`Error: ${data.error || data.message || 'Failed to generate video'}`, false, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, false, 'error');
    } finally {
        generateBtn.disabled = false;
    }
});

// Show status message
function showStatus(message, loading = false, type = '') {
    statusDiv.classList.remove('hidden');
    statusMessage.textContent = message;
    statusMessage.className = type;
    
    if (loading) {
        spinner.classList.remove('hidden');
    } else {
        spinner.classList.add('hidden');
    }
}

// Load available videos
async function loadVideos() {
    try {
        const response = await fetch(`${API_ENDPOINT}/list`);
        const videos = await response.json();
        
        if (videos && videos.length > 0) {
            resultDiv.classList.remove('hidden');
            videoList.innerHTML = videos
                .slice(0, 10)
                .map(video => `
                    <div class="video-item">
                        <h3>${video.name}</h3>
                        <a href="${video.path}" target="_blank">Watch Video</a>
                    </div>
                `)
                .join('');
        }
    } catch (error) {
        console.error('Failed to load videos:', error);
    }
}

// Load videos on page load
loadVideos();
