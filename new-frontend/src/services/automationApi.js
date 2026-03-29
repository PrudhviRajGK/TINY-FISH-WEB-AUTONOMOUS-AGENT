/**
 * Automation API Client
 * Handles Economic Times news automation endpoints
 */
import { requestJson } from './apiClient.js';
import { apiConfig } from './apiConfig.js';

const automationBaseUrl = `${apiConfig.baseUrl}/api/v1/automation`;

/**
 * Run the full automation pipeline
 * @param {Object} options - Automation options
 * @param {number} options.top_n - Number of top articles to process (1-10)
 * @param {boolean} options.auto_publish - Whether to auto-publish videos
 * @param {string[]} options.article_urls - Specific article URLs to process
 * @param {string} options.language - Language code: 'en' | 'hi' | 'te'
 * @returns {Promise<Object>} Automation response
 */
export async function runAutomation({ top_n = 3, auto_publish = false, article_urls = null, language = 'en' } = {}) {
    return requestJson(`${automationBaseUrl}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ top_n, auto_publish, article_urls, language }),
    });
}

/**
 * Get current automation status
 * @returns {Promise<Object>} Status object with is_running, current_article, progress
 */
export async function getAutomationStatus() {
    return requestJson(`${automationBaseUrl}/status`);
}

/**
 * Fetch latest Economic Times articles
 * @param {number} limit - Maximum number of articles to fetch
 * @returns {Promise<Array>} Array of article objects
 */
export async function fetchArticles(limit = 20) {
    return requestJson(`${automationBaseUrl}/articles?limit=${limit}`);
}

/**
 * Get top trending articles
 * @param {number} top_n - Number of top articles to return
 * @returns {Promise<Array>} Array of trending article objects with scores
 */
export async function getTrendingArticles(top_n = 10) {
    return requestJson(`${automationBaseUrl}/trending?top_n=${top_n}`);
}

/**
 * Test automation with a single article
 * @returns {Promise<Object>} Test results
 */
export async function testAutomation() {
    return requestJson(`${automationBaseUrl}/test`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
}
