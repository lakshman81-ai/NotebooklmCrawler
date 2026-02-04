// Centralized API Configuration

// Determine API Base URL
// Priority: Environment Variable -> Default Localhost
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Checks if the backend is reachable.
 * Returns true if the backend responds to a config load request.
 * Returns false if the request fails or times out.
 */
export async function checkBackendHealth() {
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout for quick feedback

        const response = await fetch(`${API_BASE_URL}/api/config/load`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        return response.ok;
    } catch (error) {
        // console.debug('Backend health check failed:', error);
        return false;
    }
}
