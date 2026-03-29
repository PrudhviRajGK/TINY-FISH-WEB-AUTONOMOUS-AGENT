const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();
const browserOrigin = window.location.origin;
const isLikelyViteDevServer =
    /^(http:\/\/127\.0\.0\.1:5173|http:\/\/localhost:5173|http:\/\/127\.0\.0\.1:4173|http:\/\/localhost:4173)$/.test(
        browserOrigin
    );
const fallbackBackendBaseUrl = 'http://127.0.0.1:8000';
const browserBaseUrl =
    browserOrigin.startsWith('http') && !isLikelyViteDevServer
        ? browserOrigin
        : fallbackBackendBaseUrl;

export const apiConfig = {
    baseUrl: configuredBaseUrl || browserBaseUrl,
    videosBaseUrl: `${configuredBaseUrl || browserBaseUrl}/api/v1/videos`,
};
