import { apiConfig } from '../../../services/apiConfig.js';
import { fallbackVideoCards } from '../constants/fallbackVideoCards.js';

/**
 * Transform backend video list into UI card format
 * @param {Array} videos - Array of video objects from backend
 * @param {string|null} trackedVideoFilename - Currently generating video filename
 * @returns {Array} Array of video card objects for UI
 */
export function buildLibraryCards(videos, trackedVideoFilename) {
    if (!videos || videos.length === 0) {
        return fallbackVideoCards;
    }

    return videos.map((video) => {
        const isTracked = trackedVideoFilename && video.name === trackedVideoFilename;
        const videoUrl = `${apiConfig.baseUrl}${video.path}`;
        
        // Extract topic from filename (format: topic_timestamp.mp4)
        const nameWithoutExt = video.name.replace(/\.(mp4|webm|ogg|mov|avi)$/i, '');
        const parts = nameWithoutExt.split('_');
        const timestamp = parts[parts.length - 1];
        const topicParts = parts.slice(0, -1);
        const title = topicParts.join(' ').replace(/_/g, ' ');

        // Use a gradient placeholder for thumbnail since video thumbnails don't work well
        const gradients = [
            'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        ];
        const gradientIndex = Math.abs(timestamp.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)) % gradients.length;

        return {
            id: video.name,
            title: title || 'Generated Video',
            meta: isTracked ? 'Just Created • HD 1080p' : 'Generated • HD 1080p',
            durationLabel: '00:00',
            href: videoUrl,
            imageUrl: gradients[gradientIndex],
            isTracked,
        };
    });
}
