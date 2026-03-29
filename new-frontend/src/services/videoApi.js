import { requestJson } from './apiClient.js';
import { apiConfig } from './apiConfig.js';

export async function generateVideo(payload) {
    return requestJson(`${apiConfig.videosBaseUrl}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
}

export async function listVideos() {
    const response = await requestJson(`${apiConfig.videosBaseUrl}/list`);

    if (!Array.isArray(response)) {
        throw new Error('Video list response was not a valid array.');
    }

    return response;
}

export async function getVideoStatus(videoFilename) {
    return requestJson(`${apiConfig.videosBaseUrl}/status/${videoFilename}`);
}

export async function publishVideo(videoFilename, platforms) {
    return requestJson(`${apiConfig.videosBaseUrl}/publish`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            video_filename: videoFilename,
            platforms: platforms,
        }),
    });
}

export async function deleteVideo(videoFilename) {
    return requestJson(`${apiConfig.videosBaseUrl}/delete/${videoFilename}`, {
        method: 'DELETE',
    });
}
