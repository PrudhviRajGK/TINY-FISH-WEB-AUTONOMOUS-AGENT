/**
 * Transform form values into the backend API payload format
 * @param {Object} formValues - Form values from GenerationPanel
 * @param {string} formValues.inputMode - 'topic' or 'article'
 * @param {string} formValues.topic - Video topic
 * @param {string} formValues.articleUrl - Article URL for TinyFish mode
 * @param {string} formValues.contentMode - Content mode (news, financial, corporate, educational)
 * @param {string} formValues.duration - Duration in seconds (as string)
 * @param {string} formValues.keyPoints - Key points text
 * @param {boolean} formValues.enableSubtitles - Enable subtitles
 * @param {string} formValues.voiceStyle - Voice style
 * @param {boolean} formValues.useTinyfish - Use TinyFish API
 * @param {Array<string>} formValues.publishTo - Platforms to publish to
 * @returns {Object} Payload matching VideoGenerationRequest schema
 */
export function buildVideoPayload(formValues) {
    const keyPointsArray = formValues.keyPoints
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean);

    const payload = {
        topic: formValues.inputMode === 'topic' ? formValues.topic : 'Article Video',
        duration: parseInt(formValues.duration, 10),
        key_points: keyPointsArray,
        style: formValues.contentMode || 'educational',
        use_tinyfish: formValues.useTinyfish || formValues.inputMode === 'article',
        publish_to: formValues.publishTo || [],
    };

    // Add article URL if in article mode
    if (formValues.inputMode === 'article' && formValues.articleUrl) {
        payload.article_url = formValues.articleUrl;
    }

    return payload;
}
