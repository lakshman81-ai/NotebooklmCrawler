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
    AUDIT: 'AUDIT'
};

// In-memory log storage
let logs = [];
const MAX_LOGS = 1000;
const LOGS_STORAGE_KEY = 'orchestration_cockpit_logs';

// Subscribers for real-time updates
const subscribers = new Set();

/**
 * Core logging function
 * @param {string} level - Log level (DEBUG, INFO, WARN, ERROR, AUDIT)
 * @param {string} component - Component name (e.g., 'ConfigTab', 'AutoMode')
 * @param {string} functionName - Function where log occurred
 * @param {string} message - Human-readable message
 * @param {Object} data - Additional context data
 */
export function log(level, component, functionName, message, data = {}) {
    const entry = {
        id: `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        level,
        component,
        function: functionName,
        message,
        data,
        // Workflow context
        workflow: getCurrentWorkflow(),
        // Variable snapshot (for debugging)
        variables: data.variables || null
    };

    // Add to in-memory storage
    logs.push(entry);

    // Trim if exceeds max
    if (logs.length > MAX_LOGS) {
        logs = logs.slice(-MAX_LOGS);
    }

    // Persist to localStorage
    persistLogs();

    // Notify subscribers
    subscribers.forEach(callback => callback(entry));

    // Also log to console with formatting
    const consoleMethod = level === 'ERROR' ? console.error :
        level === 'WARN' ? console.warn : console.log;
    consoleMethod(
        `[${level}] ${component}.${functionName}: ${message}`,
        data
    );

    return entry.id;
}

// Convenience methods
export const logDebug = (component, fn, msg, data) => log(LOG_LEVELS.DEBUG, component, fn, msg, data);
export const logInfo = (component, fn, msg, data) => log(LOG_LEVELS.INFO, component, fn, msg, data);
export const logWarn = (component, fn, msg, data) => log(LOG_LEVELS.WARN, component, fn, msg, data);
export const logError = (component, fn, msg, data) => log(LOG_LEVELS.ERROR, component, fn, msg, data);
export const logAudit = (component, fn, msg, data) => log(LOG_LEVELS.AUDIT, component, fn, msg, data);

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
        // Only persist last 500 logs to save space
        const toSave = logs.slice(-500);
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
            logs = JSON.parse(saved);
        }
    } catch (e) {
        console.warn('Failed to load persisted logs:', e);
    }
    return logs;
}

/**
 * Get all logs with optional filtering
 * @param {Object} filters - { level, component, startTime, endTime }
 */
export function getLogs(filters = {}) {
    let result = [...logs];

    if (filters.level) {
        result = result.filter(l => l.level === filters.level);
    }
    if (filters.component) {
        result = result.filter(l => l.component.includes(filters.component));
    }
    if (filters.startTime) {
        result = result.filter(l => new Date(l.timestamp) >= new Date(filters.startTime));
    }
    if (filters.endTime) {
        result = result.filter(l => new Date(l.timestamp) <= new Date(filters.endTime));
    }

    return result;
}

/**
 * Clear all logs
 */
export function clearLogs() {
    logs = [];
    localStorage.removeItem(LOGS_STORAGE_KEY);
    logInfo('LoggingService', 'clearLogs', 'All logs cleared', {});
}

/**
 * Export logs as JSON for debugging
 */
export function exportLogs() {
    return JSON.stringify(logs, null, 2);
}

/**
 * Subscribe to new log entries
 * @param {Function} callback - Called with each new log entry
 * @returns {Function} - Unsubscribe function
 */
export function subscribe(callback) {
    subscribers.add(callback);
    return () => subscribers.delete(callback);
}

/**
 * Get error summary for AI debugging
 */
export function getErrorSummary() {
    const errors = logs.filter(l => l.level === LOG_LEVELS.ERROR);
    return errors.map(e => ({
        timestamp: e.timestamp,
        component: e.component,
        function: e.function,
        message: e.message,
        workflow: e.workflow,
        data: e.data
    }));
}

// Initialize on load
loadPersistedLogs();
