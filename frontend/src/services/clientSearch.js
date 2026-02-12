// Client-side search service for Static Mode (GitHub Pages)

/**
 * Executes a search directly from the browser using Google Custom Search JSON API.
 * Requires API Key and CX to be set in configuration.
 */
export const searchGoogleClient = async (query, config) => {
    if (!config.googleApiKey || !config.googleCx) {
        throw new Error("Google Search API Key and Search Engine ID (CX) are required for static mode fetching. Please configure them in the 'Config' tab.");
    }

    const url = `https://www.googleapis.com/customsearch/v1?key=${config.googleApiKey}&cx=${config.googleCx}&q=${encodeURIComponent(query)}&num=5`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error?.message || "Google API request failed");
        }
        const data = await response.json();

        if (!data.items || data.items.length === 0) {
            return [];
        }

        return data.items.map(item => ({
            title: item.title,
            url: item.link,
            snippet: item.snippet
        }));
    } catch (error) {
        console.error("Client Search Error:", error);
        throw error;
    }
};

/**
 * Fallback for when no API keys are present in Static Mode.
 * Generates a direct search link.
 */
export const generateSearchLink = (query, engine = 'google') => {
    if (engine === 'bing') {
        return `https://www.bing.com/search?q=${encodeURIComponent(query)}`;
    }
    return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
};
