import { useState, useEffect, useCallback } from 'react';
import { checkBackendHealth } from '../services/apiConfig';

/**
 * Hook to monitor backend connectivity.
 * @param {number} intervalMs - Polling interval in milliseconds (default 5000)
 * @returns {Object} { isOnline, checkNow }
 */
export function useBackendStatus(intervalMs = 5000) {
    const [isOnline, setIsOnline] = useState(null); // null = initial check pending

    const checkStatus = useCallback(async () => {
        // Optimization: In static hosting environments (GitHub Pages), backend is never available.
        // Skip network request to avoid console errors.
        if (typeof window !== 'undefined' && window.location.hostname.includes('github.io')) {
            setIsOnline(false);
            return;
        }
        const status = await checkBackendHealth();
        setIsOnline(status);
    }, []);

    useEffect(() => {
        // Initial check
        checkStatus();

        // Polling
        const interval = setInterval(checkStatus, intervalMs);
        return () => clearInterval(interval);
    }, [checkStatus, intervalMs]);

    return { isOnline, checkNow: checkStatus };
}
