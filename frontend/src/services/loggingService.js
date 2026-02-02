/**
 * Orchestration Cockpit - Logging Service
 * 
 * Provides structured logging for debugging and audit trail.
 * Logs include: timestamp, level, component, function, message, data
 */

// Log levels
export const LOG_LEVELS = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARN: 'WARN',
    ERROR: 'ERROR',
    AUDIT: 'AUDIT',
    GATE: 'GATE' // Added GATE
};

// Log Categories
export const LOG_CATEGORIES = {
    DEFAULT: 'DEFAULT',
    GATE: 'GATE',
    CLICK: 'CLICK',
    NETWORK: 'NETWORK',
    MODE: 'MODE',
    TEMPLATE: 'TEMPLATE',
    FALLBACK: 'FALLBACK'
};

// In-memory log storage
let logs = [];
const MAX_LOGS = 2000; // Increased for combined logs
const LOGS_STORAGE_KEY = 'orchestration_cockpit_logs';

// Subscribers for real-time updates
const subscribers = new Set();

// Backend Polling State
let lastBackendTimestamp = null;
let pollingInterval = null;

/**
 * Generate a random correlation ID
 */
export function generateCorrelationId() {
    return 'corr_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

/**
 * Core logging function
 * @param {string} level - Log level
 * @param {string} component - Component name
 * @param {string} functionName - Function where log occurred
 * @param {string} message - Human-readable message
 * @param {Object} data - Additional context data
 * @param {string} category - Log Category
 */
export function log(level, component, functionName, message, data = {}, category = LOG_CATEGORIES.DEFAULT) {
    const entry = {
        id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        level,
        category,
        component,
        function: functionName,
        message,
        data,
        // Workflow context
        workflow: getCurrentWorkflow(),
        // Variable snapshot (for debugging)
        variables: data.variables || null,
        source: 'frontend'
    };

    addLogEntry(entry);
    return entry.id;
}

// Internal add with dedup/limit
function addLogEntry(entry) {
    logs.push(entry);

    // Sort by timestamp if needed (usually pushing is sorted, but backend logs might be slightly out of sync)
    // Actually, sorting every time is expensive. We'll trust push order or sort on read.

    // Trim if exceeds max
    if (logs.length > MAX_LOGS) {
        logs = logs.slice(-MAX_LOGS);
    }

    // Persist (debounce this if perf issues arise)
    persistLogs();

    // Notify subscribers
    notifySubscribers([entry]); // Notify with new entries

    // Console output for dev
    if (entry.source === 'frontend') {
        const consoleMethod = entry.level === 'ERROR' ? console.error :
            entry.level === 'WARN' ? console.warn : console.log;
        // consoleMethod(`[${entry.level}] ${entry.component}.${entry.function}: ${entry.message}`, entry.data);
    }
}

// Convenience methods
export const logDebug = (component, fn, msg, data) => log(LOG_LEVELS.DEBUG, component, fn, msg, data);
export const logInfo = (component, fn, msg, data) => log(LOG_LEVELS.INFO, component, fn, msg, data);
export const logWarn = (component, fn, msg, data) => log(LOG_LEVELS.WARN, component, fn, msg, data);
export const logError = (component, fn, msg, data) => log(LOG_LEVELS.ERROR, component, fn, msg, data);
export const logAudit = (component, fn, msg, data) => log(LOG_LEVELS.AUDIT, component, fn, msg, data);

// Specialized Gate Loggers
export const logGate = (component, gateName, data) => {
    log(LOG_LEVELS.GATE, component, gateName, `GATE: ${gateName}`, data, LOG_CATEGORIES.GATE);
};

export const logClick = (component, elementId, data) => {
    log(LOG_LEVELS.INFO, component, 'interaction', `Click: ${elementId}`, data, LOG_CATEGORIES.CLICK);
};

export const logNetwork = (component, url, method, data) => {
    log(LOG_LEVELS.INFO, component, 'network', `${method} ${url}`, data, LOG_CATEGORIES.NETWORK);
};

export const logFallback = (component, reason, data) => {
    log(LOG_LEVELS.WARN, component, 'fallback', `Fallback: ${reason}`, data, LOG_CATEGORIES.FALLBACK);
};

/**
 * Get current workflow context
 */
let currentWorkflow = { name: 'idle', step: 0 };

export function setWorkflow(name, step = 0) {
    currentWorkflow = { name, step, startedAt: new Date().toISOString() };
    logInfo('WorkflowManager', 'setWorkflow', `Workflow started: ${name}`, { workflow: currentWorkflow });
}

export function advanceWorkflow(stepName) {
    currentWorkflow.step++;
    currentWorkflow.currentStep = stepName;
    logInfo('WorkflowManager', 'advanceWorkflow', `Step: ${stepName}`, { workflow: currentWorkflow });
}

export function endWorkflow(success = true) {
    logInfo('WorkflowManager', 'endWorkflow',
        `Workflow ${currentWorkflow.name} ${success ? 'completed' : 'failed'}`,
        { workflow: currentWorkflow, success }
    );
    currentWorkflow = { name: 'idle', step: 0 };
}

function getCurrentWorkflow() {
    return { ...currentWorkflow };
}

/**
 * Persist logs to localStorage
 */
function persistLogs() {
    try {
        // Only persist last 200 logs to save space and avoid quota limits
        // Filter out backend logs if we want to save space?
        // No, let's keep them mixed so the view is consistent on reload.
        const toSave = logs.slice(-200);
        localStorage.setItem(LOGS_STORAGE_KEY, JSON.stringify(toSave));
    } catch (e) {
        console.warn('Failed to persist logs:', e);
    }
}

/**
 * Load logs from localStorage
 */
export function loadPersistedLogs() {
    try {
        const saved = localStorage.getItem(LOGS_STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            // Deduplicate?
            logs = parsed;
            // Update last timestamp
            if (logs.length > 0) {
                const last = logs[logs.length - 1];
                if (last.timestamp) lastBackendTimestamp = last.timestamp;
            }
        }
    } catch (e) {
        console.warn('Failed to load persisted logs:', e);
    }
    return logs;
}

/**
 * Fetch and merge backend logs
 */
export async function fetchBackendLogs() {
    try {
        let url = 'http://localhost:8000/api/logs';
        if (lastBackendTimestamp) {
            url += `?since=${encodeURIComponent(lastBackendTimestamp)}`;
        }

        const response = await fetch(url);
        if (!response.ok) return;

        const data = await response.json();
        if (data.logs && data.logs.length > 0) {
            const newLogs = data.logs.map(l => ({
                id: `be_${l.timestamp}_${Math.random().toString(36).substr(2, 5)}`, // Generate ID for keying
                ...l,
                source: 'backend',
                component: l.name || 'Backend',
                function: l.funcName || l.module || '',
                category: l.level === 'GATE' ? LOG_CATEGORIES.GATE : LOG_CATEGORIES.DEFAULT
            }));

            // Filter out logs we already have (by timestamp/content check if needed, but 'since' should handle it)
            // Just append them.

            // Update timestamp
            const lastLog = newLogs[newLogs.length - 1];
            lastBackendTimestamp = lastLog.timestamp;

            newLogs.forEach(entry => addLogEntry(entry));
        }
    } catch (e) {
        // Silent fail on polling errors
        // console.warn('Backend log poll failed', e);
    }
}

/**
 * Start polling for backend logs
 */
export function startLogPolling(intervalMs = 2000) {
    if (pollingInterval) clearInterval(pollingInterval);
    fetchBackendLogs(); // Initial fetch
    pollingInterval = setInterval(fetchBackendLogs, intervalMs);
}

export function stopLogPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

/**
 * Get all logs with optional filtering
 */
export function getLogs(filters = {}) {
    let result = [...logs];

    // Sort by timestamp desc (newest first) or asc?
    // Usually logs are viewed newest at bottom (console style) or top (activity stream).
    // Let's sort by timestamp ascending (oldest -> newest).
    result.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    if (filters.level) {
        result = result.filter(l => l.level === filters.level);
    }
    if (filters.component) {
        result = result.filter(l => l.component && l.component.toLowerCase().includes(filters.component.toLowerCase()));
    }
    if (filters.search) {
        const search = filters.search.toLowerCase();
        result = result.filter(l =>
            (l.message && l.message.toLowerCase().includes(search)) ||
            (l.data && JSON.stringify(l.data).toLowerCase().includes(search))
        );
    }

    return result;
}

/**
 * Clear all logs
 */
export function clearLogs() {
    logs = [];
    localStorage.removeItem(LOGS_STORAGE_KEY);
    lastBackendTimestamp = null; // Reset backend cursor? Or keep it to not re-fetch old logs?
    // If we clear logs, we probably want to clear the view.
    // We should probably reset timestamp so we don't re-fetch immediately unless we want to?
    // Let's keep timestamp so we only get NEW logs.

    notifySubscribers([]);
    logInfo('LoggingService', 'clearLogs', 'All logs cleared', {});
}

/**
 * Export logs as JSON
 */
export function exportLogs() {
    return JSON.stringify(logs, null, 2);
}

/**
 * Subscribe to log updates
 * @param {Function} callback - Called with (newEntries) or (allLogs)
 */
export function subscribe(callback) {
    subscribers.add(callback);
    return () => subscribers.delete(callback);
}

function notifySubscribers(newEntries) {
    subscribers.forEach(callback => callback(newEntries));
}

// Initialize
loadPersistedLogs();
