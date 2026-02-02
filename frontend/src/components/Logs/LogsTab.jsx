import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Terminal, Search, Filter, Download, Trash2, Pause, Play, ChevronRight, ChevronDown, Activity, AlertCircle, Info, Database, Layers, Copy, Check, Clock, X } from 'lucide-react';
import { getLogs, subscribe, startLogPolling, stopLogPolling, clearLogs, exportLogs, LOG_LEVELS, LOG_CATEGORIES } from '../../services/loggingService';

const LogsTab = () => {
    // State
    const [allLogs, setAllLogs] = useState([]);
    const [isPaused, setIsPaused] = useState(false);
    const [selectedLogId, setSelectedLogId] = useState(null);
    const [filters, setFilters] = useState({
        level: 'ALL',
        component: '',
        search: '',
        category: 'ALL'
    });
    const [stats, setStats] = useState({ error: 0, warn: 0, gate: 0, total: 0 });
    const [copied, setCopied] = useState(false);

    // Refs
    const logsEndRef = useRef(null);
    const scrollContainerRef = useRef(null);
    const shouldAutoScroll = useRef(true);

    // Lifecycle: Subscribe & Poll
    useEffect(() => {
        // Load initial
        setAllLogs(getLogs());
        startLogPolling(2000);

        // Subscribe
        const unsubscribe = subscribe(() => {
            if (!isPaused) {
                const updated = getLogs();
                setAllLogs(updated);
            }
        });

        return () => {
            stopLogPolling();
            unsubscribe();
        };
    }, [isPaused]);

    // Update Stats
    useEffect(() => {
        const newStats = {
            error: allLogs.filter(l => l.level === LOG_LEVELS.ERROR).length,
            warn: allLogs.filter(l => l.level === LOG_LEVELS.WARN).length,
            gate: allLogs.filter(l => l.category === LOG_CATEGORIES.GATE).length,
            total: allLogs.length
        };
        setStats(newStats);
    }, [allLogs]);

    // Auto-scroll logic
    useEffect(() => {
        if (shouldAutoScroll.current && logsEndRef.current && !isPaused) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [allLogs, isPaused]);

    // Filter Logic
    const filteredLogs = useMemo(() => {
        return allLogs.filter(log => {
            if (filters.level !== 'ALL' && log.level !== filters.level) return false;
            if (filters.category !== 'ALL' && log.category !== filters.category) return false;
            if (filters.component && !log.component.toLowerCase().includes(filters.component.toLowerCase())) return false;
            if (filters.search) {
                const searchLower = filters.search.toLowerCase();
                const matchMsg = log.message && log.message.toLowerCase().includes(searchLower);
                const matchData = log.data && JSON.stringify(log.data).toLowerCase().includes(searchLower);
                if (!matchMsg && !matchData) return false;
            }
            return true;
        });
    }, [allLogs, filters]);

    // Handlers
    const handleScroll = (e) => {
        const { scrollTop, scrollHeight, clientHeight } = e.target;
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
        shouldAutoScroll.current = isNearBottom;
    };

    const handleClear = () => {
        clearLogs();
        setAllLogs([]);
    };

    const handleExport = () => {
        const jsonString = exportLogs();
        const blob = new Blob([jsonString], { type: 'application/json' });
        const href = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = href;
        link.download = `orchestrator_logs_${new Date().toISOString()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleCopyAll = () => {
        const text = allLogs.map(l => `[${l.timestamp}] ${l.level} [${l.component}] ${l.message}`).join('\n');
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const getLevelColor = (level) => {
        switch (level) {
            case LOG_LEVELS.ERROR: return 'text-red-500 bg-red-50 border-red-100';
            case LOG_LEVELS.WARN: return 'text-amber-500 bg-amber-50 border-amber-100';
            case LOG_LEVELS.DEBUG: return 'text-slate-400 bg-slate-50 border-slate-100';
            case LOG_LEVELS.GATE: return 'text-indigo-600 bg-indigo-50 border-indigo-100';
            default: return 'text-slate-600 bg-white border-slate-100';
        }
    };

    const formatTime = (isoString) => {
        if (!isoString) return '';
        const d = new Date(isoString);
        return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
    };

    return (
        <div className="h-[calc(100vh-140px)] flex flex-col bg-slate-50 rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header / Stats Panel */}
            <div className="bg-white border-b border-slate-200 p-6 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-900 rounded-xl text-white">
                            <Terminal className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-lg font-black text-slate-900 tracking-tight">System Logs</h2>
                            <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${isPaused ? 'bg-amber-400' : 'bg-emerald-500 animate-pulse'}`} />
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                    {isPaused ? 'Paused' : 'Live Stream Active'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="h-8 w-px bg-slate-200 mx-2" />

                    <div className="flex gap-4">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Errors</span>
                            <span className="text-xl font-black text-red-500 leading-none">{stats.error}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Warnings</span>
                            <span className="text-xl font-black text-amber-500 leading-none">{stats.warn}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Gates</span>
                            <span className="text-xl font-black text-indigo-500 leading-none">{stats.gate}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Total</span>
                            <span className="text-xl font-black text-slate-700 leading-none">{stats.total}</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleCopyAll}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm"
                    >
                        {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                        {copied ? 'Copied' : 'Copy All'}
                    </button>
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm"
                    >
                        <Download className="w-4 h-4" />
                        Export
                    </button>
                    <div className="h-6 w-px bg-slate-200" />
                    <button
                        onClick={() => setIsPaused(!isPaused)}
                        className={`p-2 rounded-xl transition-all ${isPaused ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                        title={isPaused ? "Resume" : "Pause"}
                    >
                        {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                    </button>
                    <button
                        onClick={handleClear}
                        className="p-2 rounded-xl bg-slate-100 text-slate-500 hover:bg-red-50 hover:text-red-500 transition-all"
                        title="Clear Logs"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="bg-slate-50 border-b border-slate-200 p-4 flex gap-4 overflow-x-auto">
                <div className="relative group min-w-[200px]">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    <input
                        type="text"
                        placeholder="Search logs..."
                        value={filters.search}
                        onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                        className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 outline-none focus:border-indigo-500 transition-all shadow-sm placeholder:font-medium"
                    />
                </div>

                <div className="flex items-center gap-2">
                    <FilterSelect
                        label="Level"
                        value={filters.level}
                        onChange={(val) => setFilters({ ...filters, level: val })}
                        options={['ALL', 'INFO', 'WARN', 'ERROR', 'DEBUG', 'GATE']}
                    />
                    <FilterSelect
                        label="Category"
                        value={filters.category}
                        onChange={(val) => setFilters({ ...filters, category: val })}
                        options={['ALL', 'GATE', 'CLICK', 'NETWORK', 'MODE', 'TEMPLATE', 'FALLBACK']}
                    />
                    <input
                        type="text"
                        placeholder="Filter Component..."
                        value={filters.component}
                        onChange={(e) => setFilters({ ...filters, component: e.target.value })}
                        className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 outline-none focus:border-indigo-500 transition-all shadow-sm w-32"
                    />
                </div>
            </div>

            {/* Logs List */}
            <div className="flex-1 overflow-hidden flex">
                {/* List View */}
                <div
                    ref={scrollContainerRef}
                    onScroll={handleScroll}
                    className="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar"
                >
                    {filteredLogs.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-300 opacity-60">
                            <Database className="w-12 h-12 mb-4" />
                            <p className="text-sm font-black uppercase tracking-widest">No Logs Found</p>
                        </div>
                    ) : (
                        filteredLogs.map((log) => (
                            <LogEntry
                                key={log.id}
                                log={log}
                                isSelected={selectedLogId === log.id}
                                onSelect={() => setSelectedLogId(selectedLogId === log.id ? null : log.id)}
                                formatTime={formatTime}
                                getLevelColor={getLevelColor}
                            />
                        ))
                    )}
                    <div ref={logsEndRef} />
                </div>

                {/* Detail Panel (Conditionally rendered side panel) */}
                {selectedLogId && (
                    <div className="w-[400px] border-l border-slate-200 bg-white flex flex-col shadow-xl z-10 animate-in slide-in-from-right duration-300">
                        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                            <span className="text-xs font-black uppercase tracking-widest text-slate-500">Log Details</span>
                            <button onClick={() => setSelectedLogId(null)} className="text-slate-400 hover:text-slate-600">
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4">
                            {(() => {
                                const log = allLogs.find(l => l.id === selectedLogId);
                                if (!log) return null;
                                return <LogDetailView log={log} />;
                            })()}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// --- Sub-Components ---

const FilterSelect = ({ label, value, onChange, options }) => (
    <div className="relative">
        <select
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="appearance-none pl-4 pr-8 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-700 outline-none focus:border-indigo-500 transition-all shadow-sm cursor-pointer"
        >
            {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400 pointer-events-none" />
    </div>
);

const LogEntry = ({ log, isSelected, onSelect, formatTime, getLevelColor }) => {
    return (
        <div
            onClick={onSelect}
            className={`group rounded-xl border p-3 transition-all cursor-pointer font-mono text-[11px] ${isSelected
                ? 'bg-indigo-50 border-indigo-200 shadow-md ring-1 ring-indigo-500/20'
                : 'bg-white border-transparent hover:border-slate-200 hover:shadow-sm'
                }`}
        >
            <div className="flex items-start gap-3">
                <div className={`shrink-0 px-2 py-1 rounded-md border text-[9px] font-black uppercase tracking-wider w-14 text-center ${getLevelColor(log.level)}`}>
                    {log.level}
                </div>
                <div className="shrink-0 text-slate-400 font-medium w-20 pt-0.5">
                    {formatTime(log.timestamp)}
                </div>
                <div className="shrink-0 text-slate-500 font-bold w-32 truncate pt-0.5" title={log.component}>
                    {log.component}
                </div>
                <div className="flex-1 text-slate-700 break-all pt-0.5 line-clamp-2">
                    {log.message}
                </div>
                <div className="shrink-0">
                    <ChevronRight className={`w-4 h-4 text-slate-300 transition-transform ${isSelected ? 'rotate-90 text-indigo-400' : 'group-hover:text-slate-400'}`} />
                </div>
            </div>
        </div>
    );
};

const LogDetailView = ({ log }) => (
    <div className="space-y-6 font-mono text-xs">
        <div className="space-y-1">
            <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest block">Message</label>
            <div className="text-slate-800 font-medium break-words bg-slate-50 p-3 rounded-lg border border-slate-100">
                {log.message}
            </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
            <DetailItem label="Timestamp" value={log.timestamp} />
            <DetailItem label="Component" value={log.component} />
            <DetailItem label="Function" value={log.function} />
            <DetailItem label="Level" value={log.level} />
            <DetailItem label="Category" value={log.category} />
            <DetailItem label="Source" value={log.source} />
        </div>

        {log.workflow && log.workflow.name !== 'idle' && (
            <div className="space-y-2 p-3 bg-indigo-50/50 rounded-xl border border-indigo-100">
                <div className="flex items-center gap-2 text-indigo-600">
                    <Layers className="w-3 h-3" />
                    <span className="text-[10px] font-black uppercase tracking-widest">Workflow Context</span>
                </div>
                <div className="pl-5 space-y-1 text-slate-600">
                    <div>Name: <span className="font-bold">{log.workflow.name}</span></div>
                    <div>Step: {log.workflow.step}</div>
                </div>
            </div>
        )}

        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest block">Data Payload</label>
                <button
                    onClick={() => navigator.clipboard.writeText(JSON.stringify(log.data, null, 2))}
                    className="text-[9px] text-indigo-500 hover:text-indigo-700 font-bold flex items-center gap-1"
                >
                    <Copy className="w-3 h-3" /> Copy JSON
                </button>
            </div>
            <div className="bg-slate-900 text-slate-300 p-3 rounded-xl overflow-x-auto border border-slate-800">
                <pre className="text-[10px] leading-relaxed">
                    {JSON.stringify(log.data, null, 2)}
                </pre>
            </div>
        </div>
    </div>
);

const DetailItem = ({ label, value }) => (
    <div>
        <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest block">{label}</label>
        <div className="text-slate-700 font-bold truncate" title={value}>{value || '-'}</div>
    </div>
);

export default LogsTab;
