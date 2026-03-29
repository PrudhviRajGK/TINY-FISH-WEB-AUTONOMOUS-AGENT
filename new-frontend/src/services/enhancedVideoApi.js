/**
 * Enhanced Video API Service
 * Handles all backend communication for TinyFish-powered video generation
 */
import apiClient from './apiClient';

const enhancedVideoApi = {
  /**
   * Generate video from topic or article URL
   */
  generateVideo: async (payload) => {
    const response = await apiClient.post('/videos/generate', payload);
    return response.data;
  },

  /**
   * Get video generation status
   */
  getGenerationStatus: async (videoFilename) => {
    const response = await apiClient.get(`/videos/status/${videoFilename}`);
    return response.data;
  },

  /**
   * List all generated videos
   */
  listVideos: async () => {
    const response = await apiClient.get('/videos/list');
    return response.data;
  },

  /**
   * Get video details
   */
  getVideoDetails: async (videoFilename) => {
    const response = await apiClient.get(`/videos/details/${videoFilename}`);
    return response.data;
  },

  /**
   * Download video
   */
  downloadVideo: async (videoFilename) => {
    const response = await apiClient.get(`/videos/download/${videoFilename}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  /**
   * Publish video to social media platforms
   */
  publishVideo: async (videoFilename, platforms, metadata) => {
    const response = await apiClient.post('/videos/publish', {
      video_filename: videoFilename,
      platforms,
      metadata
    });
    return response.data;
  },

  /**
   * Get publishing status
   */
  getPublishingStatus: async (videoFilename) => {
    const response = await apiClient.get(`/videos/publish-status/${videoFilename}`);
    return response.data;
  },

  /**
   * Delete video
   */
  deleteVideo: async (videoFilename) => {
    const response = await apiClient.delete(`/videos/${videoFilename}`);
    return response.data;
  },

  /**
   * Preview scene images
   */
  getScenePreview: async (videoFilename) => {
    const response = await apiClient.get(`/videos/scenes/${videoFilename}`);
    return response.data;
  },

  /**
   * Regenerate specific scene
   */
  regenerateScene: async (videoFilename, sceneIndex) => {
    const response = await apiClient.post(`/videos/regenerate-scene`, {
      video_filename: videoFilename,
      scene_index: sceneIndex
    });
    return response.data;
  }
};

export default enhancedVideoApi;
