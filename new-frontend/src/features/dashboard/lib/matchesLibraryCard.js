/**
 * Check if a video card matches the search query
 * @param {Object} card - Video card object
 * @param {string} normalizedQuery - Normalized search query (lowercase, trimmed)
 * @returns {boolean} True if card matches query
 */
export function matchesLibraryCard(card, normalizedQuery) {
    if (!normalizedQuery) {
        return true;
    }

    const searchableText = [
        card.title,
        card.meta,
        card.id,
    ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

    return searchableText.includes(normalizedQuery);
}
