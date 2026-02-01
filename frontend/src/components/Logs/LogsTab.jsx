import React, { useState, useEffect, useRef } from 'react';
import { Copy, Terminal, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';

const LogsTab = () => {
    const [logs, setLogs] = useState([]);
    const [status, setStatus] = useState('IDLE');
    const [loading, setLoading] = useState(true);
    const logsEndRef = useRef(null);
    const [autoScroll, setAutoScroll] = useState(true);

    const fetchLogs = async () => {
        try {
            // Using relative path assuming proxy or same origin,
            // but bridge.py is on 8000 and vite on 5173.
            // Usually need a proxy or full URL.
            // Given the existing code doesn't show a proxy config in vite.config.js,
            // but App.jsx uses standard components.
            // I'll assume the backend is reachable at http://localhost:8000 if running locally,
            // or the deployment setup handles it.
            // Wait, looking at App.jsx, it doesn't do any fetches.
            // Dashboard.jsx likely does.
            // I should probably check how other components fetch data to be consistent.
            // But for now, I'll try to fetch from /api/logs relative to where the frontend thinks the backend is.
            // If dev, likely http://localhost:8000.

            const response = await fetch('http://localhost:8000/api/logs');
            if (response.ok) {
                const data = await response.json();
                setLogs(data.logs || []);
                setStatus(data.status || 'UNKNOWN');
            }
        } catch (error) {
            console.error('Failed to fetch logs:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 3000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (autoScroll && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, autoScroll]);

    const handleCopy = () => {
        const text = logs.join('');
        navigator.clipboard.writeText(text).then(() => {
            // Could add a toast here, but for now simple action
            alert('Logs copied to clipboard');
        });
    };

    const getStatusColor = () => {
        switch (status?.toUpperCase()) {
            case 'RUNNING': return 'text-blue-400';
            case 'COMPLETED': return 'text-emerald-400';
            case 'FAILED': return 'text-red-400';
            default: return 'text-slate-400';
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-8rem)] gap-4">
            <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-100 rounded-lg">
                        <Terminal className="w-5 h-5 text-slate-600" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-slate-800">System Logs</h2>
                        <div className="flex items-center gap-2 text-xs font-medium">
                            <span className="text-slate-500">Pipeline Status:</span>
                            <span className={`flex items-center gap-1 ${getStatusColor()}`}>
                                {status === 'RUNNING' && <RefreshCw className="w-3 h-3 animate-spin" />}
                                {status === 'COMPLETED' && <CheckCircle2 className="w-3 h-3" />}
                                {status === 'FAILED' && <AlertCircle className="w-3 h-3" />}
                                {status || 'IDLE'}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                     <button
                        onClick={() => setAutoScroll(!autoScroll)}
                        className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-colors ${
                            autoScroll
                                ? 'bg-indigo-50 text-indigo-600 border-indigo-200'
                                : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'
                        }`}
                    >
                        {autoScroll ? 'Auto-scroll On' : 'Auto-scroll Off'}
                    </button>
                    <button
                        onClick={handleCopy}
                        className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 text-white text-xs font-bold rounded-lg hover:bg-slate-800 transition-colors shadow-sm"
                    >
                        <Copy className="w-3 h-3" />
                        Copy Output
                    </button>
                </div>
            </div>

            <div className="flex-1 bg-[#1e1e1e] rounded-xl shadow-inner border border-slate-800 overflow-hidden flex flex-col relative group">
                <div className="absolute top-0 left-0 right-0 h-6 bg-[#252526] flex items-center px-4 border-b border-[#333] z-10">
                    <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></div>
                    </div>
                    <div className="mx-auto text-[#888] text-[10px] font-mono">pipeline.log</div>
                </div>

                <div className="flex-1 overflow-auto p-4 pt-8 font-mono text-sm">
                    {logs.length === 0 ? (
                        <div className="text-slate-500 italic">Waiting for logs...</div>
                    ) : (
                        logs.map((line, index) => (
                            <div key={index} className="text-slate-300 hover:bg-[#2a2a2a] px-1 rounded leading-relaxed whitespace-pre-wrap break-all">
                                <span className="text-slate-600 select-none w-8 inline-block text-right mr-3 text-xs opacity-50">{index + 1}</span>
                                {line}
                            </div>
                        ))
                    )}
                    <div ref={logsEndRef} />
                </div>
            </div>
        </div>
    );
};

export default LogsTab;
