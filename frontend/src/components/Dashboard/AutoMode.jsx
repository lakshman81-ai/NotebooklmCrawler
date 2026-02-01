import React, { useState, useEffect } from 'react';
import { Play, ShieldCheck, Activity, Terminal, Globe, Bot, Download, Check, Link as LinkIcon, Search, Layers, FileText, Cpu, Zap, AlertCircle, AlertTriangle, CheckCircle, BookOpen, HelpCircle, Layout, ClipboardList, Folder, ChevronRight, X, Copy, StickyNote, Clipboard } from 'lucide-react';

// --- Guided Mode Popup Component ---
const GuidedModePopup = ({ isOpen, onClose, context }) => {
    const [logs, setLogs] = useState([]);
    const [copiedOutput, setCopiedOutput] = useState(false);
    const [outputPromptText, setOutputPromptText] = useState('');

    // Generate Input Sources Keywords
    const generateInputPrompt = () => {
        const parts = [];
        if (context.targetUrls) parts.push(context.targetUrls);
        if (context.topic) parts.push(`Topic: ${context.topic}`);
        if (context.grade) parts.push(`Grade: ${context.grade}`);
        if (context.subject) parts.push(`Subject: ${context.subject}`);
        if (context.subtopics) parts.push(`Subtopics: ${context.subtopics}`);
        if (context.keywordsScrape) parts.push(`Keywords: ${context.keywordsScrape}`);
        return parts.length > 0 ? parts.join('\n') : 'No input keywords configured';
    };

    // Generate Output Report Keywords
    const generateOutputPrompt = () => {
        const tasks = [];

        // Difficulty level
        const diffMap = {
            'Identify': 'Focus on definitions, basic facts, and identification of key terms. (Easy Level)',
            'Connect': 'Focus on relationships, cause-and-effect, and connecting concepts. (Medium Level)',
            'Extend': 'Focus on applications, scenario-based analysis, and extending concepts. (Hard Level)'
        };
        tasks.push(`[DIFFICULTY: ${context.difficulty || 'Connect'}]\n${diffMap[context.difficulty] || diffMap['Connect']} `);

        if (context.outputs?.studyGuide) {
            tasks.push('[TASK: STUDY GUIDE]\nCreate a detailed study guide extracting Anchor Concepts and key definitions.');
        }
        if (context.outputs?.quiz) {
            const q = context.quizConfig || {};
            tasks.push(`[TASK: QUIZ]\nCreate a quiz with ${q.mcq || 10} MCQs, ${q.ar || 5} Assertion - Reasoning, and ${q.detailed || 3} Detailed Answer questions.Include Answer Key.`);
        }
        if (context.outputs?.handout) {
            tasks.push('[TASK: HANDOUT]\nCreate a Visual Handout with a one-page summary and diagrams.');
        }
        if (context.keywordsReport) {
            tasks.push(`[FOCUS KEYWORDS]: ${context.keywordsReport} `);
        }
        if (context.quizConfig?.custom) {
            tasks.push(`[CUSTOM INSTRUCTIONS]: ${context.quizConfig.custom} `);
        }

        return tasks.join('\n\n');
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setCopiedOutput(true);
        setTimeout(() => setCopiedOutput(false), 2000);
    };

    const inputPrompt = generateInputPrompt();
    const outputPrompt = generateOutputPrompt();

    // Initialize outputPromptText with generated prompt when it changes
    useEffect(() => {
        setOutputPromptText(outputPrompt);
    }, [outputPrompt]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-[2rem] w-full max-w-3xl max-h-[80vh] overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-amber-50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-amber-500 rounded-xl text-white">
                            <Bot className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="text-lg font-black text-slate-800">NotebookLM Guided Mode</h2>
                            <p className="text-xs text-slate-500">Copy prompts below and paste into NotebookLM manually</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-xl transition-colors">
                        <X className="w-5 h-5 text-slate-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6 overflow-y-auto max-h-[60vh]">
                    {/* Input Basis (Read-only, no copy button) */}
                    <div className="space-y-3">
                        <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                            Input Basis
                        </label>
                        <textarea
                            readOnly
                            value={inputPrompt}
                            className="w-full h-32 p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-mono text-slate-700 resize-none focus:outline-none"
                        />
                        <p className="text-[10px] text-slate-400 italic">
                            Read-only source information
                        </p>
                    </div>

                    {/* Output Prompt (Editable, copy icon top-right) */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                                Output Prompt
                            </label>
                            <button
                                onClick={() => copyToClipboard(outputPromptText)}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${copiedOutput
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-slate-100 text-slate-600 hover:bg-indigo-100 hover:text-indigo-700'
                                    }`}
                            >
                                {copiedOutput ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                {copiedOutput ? 'Copied!' : 'Copy'}
                            </button>
                        </div>
                        <textarea
                            value={outputPromptText}
                            onChange={(e) => setOutputPromptText(e.target.value)}
                            className="w-full h-48 p-4 bg-white border-2 border-indigo-200 rounded-xl text-sm font-mono text-slate-700 resize-y focus:outline-none focus:border-indigo-500"
                            placeholder="Edit the output prompt as needed..."
                        />
                        <p className="text-[10px] text-slate-400 italic">
                            Paste this into NotebookLM's "Create Your Own" report prompt, then click Generate
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-200 bg-slate-50">
                    <div className="flex items-center justify-between">
                        <p className="text-xs text-slate-500">
                            <span className="font-bold">Steps:</span> 1. Add sources → 2. Click "Notebook guide" → 3. "Create Your Own" → 4. Paste output prompt → 5. Generate
                        </p>
                        <button
                            onClick={onClose}
                            className="px-6 py-2 bg-indigo-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-indigo-500 transition-all"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- Sub-components ---

const TabButton = ({ label, active, onClick, icon }) => (
    <button
        onClick={onClick}
        className={`flex-1 flex items-center justify-center gap-3 py-6 relative transition-all duration-300 group ${active ? 'bg-white text-indigo-900' : 'bg-transparent text-slate-400 hover:bg-white/5 hover:text-indigo-300'}`}
    >
        <div className={`p-2 rounded-xl transition-all ${active ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-800 text-slate-500 group-hover:bg-indigo-900/50 group-hover:text-indigo-400'}`}>
            {icon}
        </div>
        <span className="text-xs font-black uppercase tracking-widest">{label}</span>
        {active && <div className="absolute bottom-0 left-0 w-full h-1 bg-indigo-600 rounded-t-full shadow-[0_-4px_12px_rgba(79,70,229,0.5)]"></div>}
    </button>
);

const SegmentedControl = ({ options, value, onChange }) => (
    <div className="flex gap-2 p-1.5 bg-slate-100 rounded-[1.5rem] border border-slate-200/50 shadow-inner">
        {options.map((opt) => (
            <button
                key={opt.value}
                onClick={() => onChange(opt.value)}
                className={`flex-1 py-3 px-2 rounded-[1.2rem] text-[10px] font-black uppercase tracking-widest transition-all duration-300 flex items-center justify-center gap-2 ${value === opt.value
                    ? 'bg-white text-indigo-700 shadow-lg shadow-indigo-100 ring-1 ring-black/5'
                    : 'text-slate-400 hover:text-slate-600'
                    }`}
            >
                {opt.icon && <opt.icon className={`w-3.5 h-3.5 ${value === opt.value ? 'text-indigo-500' : 'text-slate-300'}`} />}
                {opt.label}
            </button>
        ))}
    </div>
);

const SidebarLink = ({ label, icon, onClick, active }) => (
    <button
        onClick={onClick}
        className={`w - full flex flex - col items - center gap - 2 py - 4 transition - all duration - 200 group relative ${active ? 'text-indigo-400' : 'text-slate-500 hover:text-slate-300'} `}
    >
        <div className={`p - 3 rounded - 2xl transition - all ${active ? 'bg-indigo-500/10 text-indigo-400 shadow-glow' : 'bg-transparent group-hover:bg-white/5'} `}>
            {icon}
        </div>
        <span className={`text - [9px] font - black uppercase tracking - widest transition - opacity ${active ? 'text-white' : 'text-slate-600 group-hover:text-slate-400'} `}>{label}</span>
        {active && <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-indigo-500 rounded-l-full"></div>}
    </button>
);

const InputField = ({ label, value, onChange, placeholder, type = "text", required = false, minLength, error, disabled = false }) => (
    <div className={`space-y-2 ${disabled ? 'opacity-50 pointer-events-none grayscale' : ''}`}>
        <div className="flex justify-between items-center pl-1">
            <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">
                {label} {required && <span className="text-red-400">*</span>}
            </label>
            {error && <span className="text-[9px] font-bold text-red-500 uppercase flex items-center gap-1"><AlertCircle className="w-3 h-3" /> {error}</span>}
        </div>
        <div className="relative group">
            <input
                type={type}
                className={`w-full px-5 py-4 bg-slate-50 border ${error ? 'border-red-300 focus:border-red-500' : 'border-slate-200 focus:border-indigo-600'} rounded-2xl outline-none font-bold text-slate-700 text-sm shadow-sm transition-all focus:ring-4 focus:ring-indigo-50 placeholder:text-slate-300 focus:bg-white`}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                disabled={disabled}
            />
            {value && !error && !disabled && (
                <div className="absolute right-4 top-4 text-emerald-500 animate-in zoom-in duration-300">
                    <CheckCircle className="w-5 h-5" />
                </div>
            )}
        </div>
    </div>
);

// TextAreaField for long URLs and multi-line inputs
const TextAreaField = ({ label, value, onChange, placeholder, required = false, error, disabled = false, rows = 3 }) => (
    <div className={`space-y-2 ${disabled ? 'opacity-50 pointer-events-none grayscale' : ''}`}>
        <div className="flex justify-between items-center pl-1">
            <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em]">
                {label} {required && <span className="text-red-400">*</span>}
            </label>
            {error && <span className="text-[9px] font-bold text-red-500 uppercase flex items-center gap-1"><AlertCircle className="w-3 h-3" /> {error}</span>}
        </div>
        <div className="relative group">
            <textarea
                rows={rows}
                className={`w-full px-5 py-4 bg-slate-50 border ${error ? 'border-red-300 focus:border-red-500' : 'border-slate-200 focus:border-indigo-600'} rounded-2xl outline-none font-medium text-slate-700 text-sm shadow-sm transition-all focus:ring-4 focus:ring-indigo-50 placeholder:text-slate-300 focus:bg-white resize-y min-h-[80px]`}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                disabled={disabled}
            />
            {value && !error && !disabled && (
                <div className="absolute right-4 top-4 text-emerald-500 animate-in zoom-in duration-300">
                    <CheckCircle className="w-5 h-5" />
                </div>
            )}
        </div>
    </div>
);

// --- Main Component ---

const AutoMode = () => {
    // Top-Level State
    const [activeTab, setActiveTab] = useState('INPUT'); // 'INPUT' | 'OUTPUT'
    const [status, setStatus] = useState('IDLE'); // 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED'
    const [progress, setProgress] = useState(0);
    const [progressLabel, setProgressLabel] = useState('SYSTEM READY'); // New state for technical label
    const [results, setResults] = useState(null); // New state to hold execution results
    const [showGuidedPopup, setShowGuidedPopup] = useState(false); // Guided Mode popup
    const [logs, setLogs] = useState([]);

    // Output View State
    const [outputView, setOutputView] = useState('SYNTHESIS'); // 'SYNTHESIS' | 'RAW' | 'SOURCE' | 'OUTPUT'

    // Settings Overlay
    const [showSettings, setShowSettings] = useState(false);

    // Form Context (Strict Order)
    const [context, setContext] = useState({
        // Refinement: Add 'searchWeb' Toggle & 'Target URLs'
        searchWeb: false, // Default OFF
        targetUrls: '', // Comma separated URLs

        grade: '', // 3-9
        subject: '', // Physics, Math, Chem, Bio, Grammar
        topic: '', // Min 3 chars
        subtopics: '',
        intelligenceSource: 'NOTEBOOKLM', // Refinement: Default NOTEBOOKLM
        keywordsScrape: '',
        keywordsReport: '',
        localFilePath: '',
        outputs: {
            studyGuide: true,
            quiz: true,
            handout: false
        },
        quizConfig: {
            mcq: 10,
            ar: 5,
            detailed: 3,
            custom: ''
        },
        difficulty: 'Connect' // Identify (Easy), Connect (Medium), Extend (Hard)
    });

    // Validation State
    const [errors, setErrors] = useState({});

    // Configuration (System)
    const [config, setConfig] = useState({
        maxTokens: 2000,
        strategy: 'section_aware', // section_aware | raw_dump
        model: 'gpt-4-turbo',
        headless: false,
        chromeUserDataDir: '',
        discoveryMethod: 'notebooklm',
        notebooklmAvailable: true,
        deepseekAvailable: false, // Default OFF - failures common
        notebooklmGuided: false   // Guided mode: clipboard keywords, user clicks Generate
    });

    // Load config from backend on mount
    useEffect(() => {
        const loadConfig = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/config/load');
                if (response.ok) {
                    const data = await response.json();
                    setConfig(prev => ({
                        ...prev,
                        maxTokens: data.maxTokens,
                        strategy: data.strategy,
                        headless: data.headless,
                        chromeUserDataDir: data.chromeUserDataDir,
                        discoveryMethod: data.discoveryMethod,
                        notebooklmAvailable: data.notebooklmAvailable,
                        deepseekAvailable: data.deepseekAvailable,
                        notebooklmGuided: data.notebooklmGuided || false
                    }));
                }
            } catch (e) {
                console.log('Config load skipped (backend not running)');
            }
        };
        loadConfig();
    }, []);

    // Load context from localStorage on mount
    useEffect(() => {
        const savedContext = localStorage.getItem('dashboard_context');
        if (savedContext) {
            try {
                const parsed = JSON.parse(savedContext);
                setContext(prev => ({ ...prev, ...parsed }));
            } catch (e) {
                console.error('Failed to load saved context:', e);
            }
        }
    }, []);

    // Save context to localStorage whenever it changes
    useEffect(() => {
        localStorage.setItem('dashboard_context', JSON.stringify(context));
    }, [context]);

    // --- Validation Logic (Gate 2) ---
    const validateInput = () => {
        const newErrors = {};
        const validGrades = ['3', '4', '5', '6', '7', '8', '9'];

        // Logic: If Search Web is ON, validate Grade/Subject. Else, validate TargetURL.
        if (context.searchWeb) {
            if (!context.grade) newErrors.grade = "Required for Web Search";
            else if (!validGrades.includes(context.grade)) newErrors.grade = "Grade 3-9 Only";

            if (!context.subject) newErrors.subject = "Required for Web Search";

            if (!context.topic) newErrors.topic = "Required";
            else if (context.topic.length < 3) newErrors.topic = "Min 3 chars";
        } else {
            // Direct URL mode
            if (!context.targetUrls && !context.localFilePath) {
                // Eventually we might allow local file path only too.
                // For now, if no local file, require URL.
                if (!context.localFilePath && !context.topic) {
                    // Topic acts as a fallback or title
                    newErrors.targetUrls = "Provide URLs or Local Path";
                }
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const checkStatus = async () => {
        try {
            const baseUrl = `http://localhost:8000`; // Ensure port matches backend
            const response = await fetch(`${baseUrl}/api/logs`);
            const data = await response.json();

            if (data.logs) {
                setLogs(data.logs);

                // Parse logs for progress & label
                const lastLog = data.logs[data.logs.length - 1] || "";

                if (lastLog.includes("NotebookLM")) { setProgress(30); setProgressLabel("NOTEBOOKLM_DRIVER_ACTIVE"); }
                else if (lastLog.includes("uploaded") || lastLog.includes("Source Discovery")) { setProgress(50); setProgressLabel("SOURCE_ACQUISITION"); }
                else if (lastLog.includes("Chat processed") || lastLog.includes("Report Generation")) { setProgress(70); setProgressLabel("INFERENCE_ENGINE_PROCESSING"); }
                else if (lastLog.includes("Saved") || lastLog.includes("Exporting report")) { setProgress(90); setProgressLabel("ARTIFACT_SERIALIZATION"); }

                if (data.status === 'COMPLETED') {
                    setStatus('COMPLETED');
                    setProgress(100);
                    setProgressLabel("MISSION_COMPLETE");
                    setResults({ timestamp: new Date(), artifacts: true }); // Mock result presence
                } else if (data.status === 'FAILED') {
                    setStatus('FAILED');
                    setProgressLabel("MISSION_FAILED");
                }
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    };

    useEffect(() => {
        let interval;
        if (status === 'RUNNING') {
            interval = setInterval(checkStatus, 2000);
        }
        return () => clearInterval(interval);
    }, [status]);

    const handleOpenFolder = async (path) => {
        try {
            await fetch(`http://localhost:8000/api/explore?path=${encodeURIComponent(path)}`);
        } catch (e) {
            console.error("Failed to open folder", e);
        }
    };

    const handleLaunch = async () => {
        if (!validateInput()) {
            setLogs(prev => [`[VALIDATION_ERROR] Check input fields`, ...prev]);
            return;
        }

        // If Guided Mode is enabled, show the popup instead of running the pipeline
        if (config.notebooklmGuided) {
            setShowGuidedPopup(true);
            setLogs(prev => ['[GUIDED MODE] Showing prompts for manual NotebookLM use', ...prev]);
            return;
        }

        setStatus('RUNNING');
        setActiveTab('INPUT');
        setProgress(5);
        setLogs(['[SYSTEM] Initiating mission protocol...', `[CONFIG] Source: ${context.intelligenceSource} | Web Search: ${context.searchWeb ? 'ON' : 'OFF'}`]);

        if (!context.searchWeb && context.targetUrls) {
            setLogs(prev => [`[TARGET] Explicit URLs detected: ${context.targetUrls.split(',').length} sources`, ...prev]);
        }

        try {
            const baseUrl = `http://${window.location.hostname}:3000`; // Use 8000 for backend? Usually 8000. Assuming vite proxy or direct.
            // Adjust to 8000 if not proxied.
            const backendUrl = `http://localhost:8000`;

            const response = await fetch(`${backendUrl}/api/auto/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    targetUrl: context.searchWeb ? '' : context.targetUrls, // Pass explicit URLs if Web Search is OFF
                    grade: context.grade || 'General',
                    topic: context.topic || 'Analysis',
                    subtopics: context.subtopics,
                    materialType: 'mixed_outputs',
                    customPrompt: context.quizConfig.custom,
                    sourceType: context.intelligenceSource.toLowerCase(),
                    config: {
                        ...config,
                        headless: config.headless,
                        discoveryMethod: (context.intelligenceSource === 'AUTO' || context.intelligenceSource === 'GOOGLE' || context.intelligenceSource === 'DDG')
                            ? (context.searchWeb ? 'Auto' : 'Direct')
                            : config.discoveryMethod || 'notebooklm', // Use config value
                        outputs: context.outputs,
                        quizConfig: context.quizConfig,
                        difficulty: context.difficulty,
                        keywordsReport: context.keywordsReport,
                        localFilePath: context.localFilePath,
                        modes: {
                            D: config.notebooklmAvailable
                        }
                    }
                })
            });

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.detail || 'Execution failed');
            }
        } catch (error) {
            setLogs(prev => [`[CRITICAL] ${error.message}`, ...prev]);
            setStatus('FAILED');
        }
    };

    // Copy Logs Feature
    const copyLogs = () => {
        const text = logs.join('\n');
        navigator.clipboard.writeText(text);
        setLogs(prev => ['[SYSTEM] Logs copied to clipboard', ...prev]);
    };

    return (
        <div className="flex h-[880px] bg-slate-900 rounded-[3rem] overflow-hidden shadow-2xl border border-slate-800 font-sans relative">

            {/* Guided Mode Popup */}
            <GuidedModePopup
                isOpen={showGuidedPopup}
                onClose={() => setShowGuidedPopup(false)}
                context={context}
                config={config}
            />

            {/* --- 1. Global Control Sidebar (Fixed) --- */}
            <div className="w-24 bg-slate-950 border-r border-slate-800/50 flex flex-col items-center py-10 z-20">
                <div className="p-3 bg-indigo-600 rounded-xl mb-12 shadow-lg shadow-indigo-500/20">
                    <Activity className="w-6 h-6 text-white" />
                </div>

                <div className="flex-1 w-full space-y-4 px-2">
                    {/* Navigation Items REMOVED as per user request */}
                </div>

            </div>

            {/* --- Main Workspace (Right Side) --- */}
            <div className="flex-1 flex flex-col bg-slate-50 relative overflow-hidden">

                {/* Tabs Header */}
                <div className="h-24 bg-slate-900 flex items-end px-8 gap-8 border-b border-white/5 pb-0">
                    <div className="flex-1 flex gap-4 translate-y-[1px]">
                        <TabButton
                            label="INPUT (Research)"
                            active={activeTab === 'INPUT'}
                            onClick={() => setActiveTab('INPUT')}
                            icon={<Search className="w-4 h-4" />}
                        />
                        <TabButton
                            label="OUTPUT (Synthesis)"
                            active={activeTab === 'OUTPUT'}
                            onClick={() => setActiveTab('OUTPUT')}
                            icon={<Layers className="w-4 h-4" />}
                        />
                    </div>
                    {/* Status Pill (Enhanced) */}
                    <div className="py-6 mb-2">
                        <div className={`px-6 py-3 rounded-2xl border flex items-center gap-4 transition-all ${status === 'RUNNING' ? 'bg-amber-50/10 border-amber-500/30' : 'bg-slate-800/50 border-slate-700'}`}>
                            <div className="text-right">
                                <div className={`text-[10px] font-black uppercase tracking-widest ${status === 'RUNNING' ? 'text-amber-400' : 'text-slate-400'}`}>
                                    {status === 'IDLE' ? 'SYSTEM READY' : status}
                                </div>
                                <div className="text-[9px] font-bold text-slate-500 mt-0.5 font-mono">{progressLabel}</div>
                            </div>
                            <div className="relative w-10 h-10 flex items-center justify-center">
                                <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 36 36">
                                    <path className="text-slate-700" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" />
                                    <path className={`${status === 'RUNNING' ? 'text-amber-500' : 'text-slate-600'} transition-all duration-500`} strokeDasharray={`${progress}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="4" />
                                </svg>
                                <div className={`text-[9px] font-black absolute ${status === 'RUNNING' ? 'text-amber-400' : 'text-slate-500'}`}>{progress}%</div>
                            </div>
                        </div>
                    </div>
                </div >

                {/* --- TAB CONTENT AREA --- */}
                < div className="flex-1 overflow-hidden relative" >

                    {/* === INPUT TAB === */}
                    < div className={`absolute inset-0 p-8 grid grid-cols-12 grid-rows-[1fr_auto] gap-8 text-left transition-all duration-500 transform ${activeTab === 'INPUT' ? 'translate-x-0 opacity-100' : '-translate-x-10 opacity-0 pointer-events-none'}`}>

                        {/* LEFT COLUMN: Research Foundation & Config (Scrollable) */}
                        < div className="col-span-7 row-start-1 h-full overflow-y-auto pr-4 custom-scrollbar pb-4" >

                            {/* 1. Research Foundation Card */}
                            < div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-200 space-y-8" >
                                <div className="flex items-center justify-between border-b border-slate-100 pb-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                                            <BookOpen className="w-5 h-5" />
                                        </div>
                                        <h2 className="text-xl font-black text-slate-800 tracking-tight">Research Foundation</h2>
                                    </div>

                                    {/* Refinement: Search Web Toggle */}
                                    <div className="flex items-center gap-3 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
                                        <span className={`text-[9px] font-black uppercase tracking-widest ${context.searchWeb ? 'text-indigo-600' : 'text-slate-400'}`}>Search Web</span>
                                        <button
                                            onClick={() => setContext({ ...context, searchWeb: !context.searchWeb })}
                                            className={`w-10 h-5 rounded-full relative transition-colors ${context.searchWeb ? 'bg-indigo-500' : 'bg-slate-300'}`}
                                        >
                                            <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${context.searchWeb ? 'left-6' : 'left-1'}`} />
                                        </button>
                                    </div>
                                </div>

                                {/* Refinement: Target URLs (Visible when Web Search OFF) */}
                                {
                                    !context.searchWeb && (
                                        <div className="animate-in slide-in-from-top-2">
                                            <TextAreaField
                                                label="Target URLs (Comma separated)"
                                                placeholder="https://example.com/a, https://example.com/b..."
                                                value={context.targetUrls}
                                                onChange={(e) => setContext({ ...context, targetUrls: e.target.value })}
                                                error={errors.targetUrls}
                                                rows={2}
                                            />
                                            <div className="text-[9px] text-slate-400 font-bold mt-1 text-right">Enabled for Direct Extraction</div>
                                        </div>
                                    )
                                }

                                <div className={`space-y-6 transition-all duration-300 ${!context.searchWeb ? 'opacity-50 grayscale' : ''}`}>
                                    {/* (0) Grade */}
                                    {/* Disabled if Search Web is OFF */}
                                    <div className="grid grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <div className="flex justify-between pl-1">
                                                <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Grade (3-9)*</label>
                                                {errors.grade && <span className="text-[9px] text-red-500 font-bold">{errors.grade}</span>}
                                            </div>
                                            <select
                                                value={context.grade}
                                                onChange={(e) => setContext({ ...context, grade: e.target.value })}
                                                disabled={!context.searchWeb}
                                                className={`w-full p-4 bg-slate-50 rounded-2xl font-bold text-slate-700 border ${errors.grade ? 'border-red-300' : 'border-slate-200'} outline-none focus:border-indigo-500 appearance-none disabled:cursor-not-allowed`}
                                            >
                                                <option value="">Select Grade...</option>
                                                {[3, 4, 5, 6, 7, 8, 9].map(g => <option key={g} value={g}>Grade {g}</option>)}
                                            </select>
                                        </div>

                                        {/* (1) Subject (Refinement: Editable) */}
                                        <div className="space-y-2">
                                            <div className="flex justify-between pl-1">
                                                <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Subject*</label>
                                                {errors.subject && <span className="text-[9px] text-red-500 font-bold">{errors.subject}</span>}
                                            </div>
                                            <div className="relative">
                                                <input
                                                    list="subjects-list"
                                                    value={context.subject}
                                                    onChange={(e) => setContext({ ...context, subject: e.target.value })}
                                                    disabled={!context.searchWeb}
                                                    placeholder="Select or Type..."
                                                    className={`w-full p-4 bg-slate-50 rounded-2xl font-bold text-slate-700 border ${errors.subject ? 'border-red-300' : 'border-slate-200'} outline-none focus:border-indigo-500 disabled:cursor-not-allowed`}
                                                />
                                                <datalist id="subjects-list">
                                                    {['Physics', 'Math', 'Chemistry', 'Biology', 'Grammar', 'History', 'Geography'].map(s => <option key={s} value={s} />)}
                                                </datalist>
                                            </div>
                                        </div>
                                    </div>

                                    {/* (2) Topic */}
                                    <InputField
                                        label="Topic Source"
                                        placeholder="Enter main topic..."
                                        value={context.topic}
                                        onChange={(e) => setContext({ ...context, topic: e.target.value })}
                                        required={context.searchWeb}
                                        error={errors.topic}
                                        disabled={!context.searchWeb && !context.localFilePath && !context.targetUrls} // Enable if needed as title
                                    />

                                    {/* (3) Sub-Topics */}
                                    <InputField
                                        label="Sub-Topics (Optional)"
                                        placeholder="Add specific sub-keywords..."
                                        value={context.subtopics}
                                        onChange={(e) => setContext({ ...context, subtopics: e.target.value })}
                                        disabled={!context.searchWeb}
                                    />
                                </div>

                                {/* Difficulty Engine (Always Active) */}
                                <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 flex items-center justify-between">
                                    <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Logic Difficulty</label>
                                    <div className="flex gap-2">
                                        {['Identify', 'Connect', 'Extend'].map(level => (
                                            <button
                                                key={level}
                                                onClick={() => setContext({ ...context, difficulty: level })}
                                                className={`px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${context.difficulty === level ? 'bg-white text-indigo-600 shadow-md ring-1 ring-black/5' : 'text-slate-400 hover:text-slate-600'}`}
                                            >
                                                {level}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div >

                            {/* Intelligence Source (Consolidated) */}
                            < div className="space-y-3 px-2" >
                                <label className="text-[9px] font-black text-slate-400 uppercase tracking-[0.3em] pl-2">Intelligence Source</label>
                                <SegmentedControl
                                    options={[
                                        { label: 'AUTO', value: 'AUTO' },
                                        { label: 'GOOGLE', value: 'GOOGLE' },
                                        { label: 'DUCKDUCKGO', value: 'DDG' },
                                        { label: 'NOTEBOOKLM', value: 'NOTEBOOKLM', icon: Bot }
                                    ]}
                                    value={context.intelligenceSource}
                                    onChange={(val) => setContext({ ...context, intelligenceSource: val })}
                                />
                            </div >

                            {/* Customization Cluster */}
                            < div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-200 space-y-6" >
                                <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Extraction Rules</h3>
                                <div className="grid grid-cols-2 gap-6">
                                    <InputField label="Keywords to Scrape" placeholder="Specific terms..." value={context.keywordsScrape} onChange={(e) => setContext({ ...context, keywordsScrape: e.target.value })} />
                                    <InputField label="Keywords for Report" placeholder="Reporting focus..." value={context.keywordsReport} onChange={(e) => setContext({ ...context, keywordsReport: e.target.value })} />
                                </div>
                                <InputField label="Local File Path" placeholder="C:/Data/..." value={context.localFilePath} onChange={(e) => setContext({ ...context, localFilePath: e.target.value })} />
                            </div >

                        </div >

                        {/* RIGHT COLUMN: Output Config & Activity Stream (40%) */}
                        < div className="col-span-5 row-start-1 h-full flex flex-col gap-6 overflow-hidden" >

                            {/* Expected Output Card */}
                            < div className="bg-white p-8 rounded-[2.5rem] shadow-sm border border-slate-200 flex-shrink-0" >
                                <div className="flex items-center gap-3 mb-6">
                                    <CheckCircle className="w-5 h-5 text-indigo-500" />
                                    <h3 className="text-sm font-black text-slate-800 uppercase tracking-wide">Expected Output</h3>
                                </div>
                                <div className="space-y-4">
                                    {['Study Guide', 'Quiz', 'Handout'].map(opt => {
                                        const key = opt.toLowerCase().replace(' ', '') === 'studyguide' ? 'studyGuide' : opt.toLowerCase().replace(' ', '');
                                        const isQuiz = key === 'quiz';

                                        return (
                                            <div key={key} className={`p-4 rounded-2xl border transition-all ${context.outputs[isQuiz ? 'quiz' : key] ? 'bg-indigo-50 border-indigo-200' : 'bg-slate-50 border-slate-100'}`}>
                                                <div
                                                    className="flex items-center gap-3 cursor-pointer"
                                                    onClick={() => setContext({ ...context, outputs: { ...context.outputs, [isQuiz ? 'quiz' : key]: !context.outputs[isQuiz ? 'quiz' : key] } })}
                                                >
                                                    <div className={`w-5 h-5 rounded-lg border flex items-center justify-center transition-colors ${context.outputs[isQuiz ? 'quiz' : key] ? 'bg-indigo-600 border-indigo-600' : 'bg-white border-slate-300'}`}>
                                                        {context.outputs[isQuiz ? 'quiz' : key] && <Check className="w-3 h-3 text-white" />}
                                                    </div>
                                                    <span className={`text-xs font-bold uppercase tracking-wider ${context.outputs[isQuiz ? 'quiz' : key] ? 'text-indigo-900' : 'text-slate-500'}`}>{opt}</span>
                                                </div>

                                                {/* Expanded Quiz Options (Refinement: 1x4 Layout) */}
                                                {isQuiz && context.outputs.quiz && (
                                                    <div className="mt-4 pl-8 grid grid-cols-4 gap-2 animate-in slide-in-from-top-2">
                                                        <div className="space-y-1">
                                                            <label className="text-[7px] font-bold text-indigo-400 uppercase truncate">MCQ</label>
                                                            <input type="number" className="w-full p-2 rounded-lg bg-white border border-indigo-100 text-[10px] font-bold text-indigo-800 text-center" value={context.quizConfig.mcq} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, mcq: e.target.value } })} />
                                                        </div>
                                                        <div className="space-y-1">
                                                            <label className="text-[7px] font-bold text-indigo-400 uppercase truncate">Reason</label>
                                                            <input type="number" className="w-full p-2 rounded-lg bg-white border border-indigo-100 text-[10px] font-bold text-indigo-800 text-center" value={context.quizConfig.ar} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, ar: e.target.value } })} />
                                                        </div>
                                                        <div className="space-y-1">
                                                            <label className="text-[7px] font-bold text-indigo-400 uppercase truncate">Detail</label>
                                                            <input type="number" className="w-full p-2 rounded-lg bg-white border border-indigo-100 text-[10px] font-bold text-indigo-800 text-center" value={context.quizConfig.detailed} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, detailed: e.target.value } })} />
                                                        </div>
                                                        <div className="space-y-1">
                                                            <label className="text-[7px] font-bold text-indigo-400 uppercase truncate">Blanks</label>
                                                            <input type="text" className="w-full p-2 rounded-lg bg-white border border-indigo-100 text-[10px] font-bold text-indigo-800 text-center" placeholder="..." value={context.quizConfig.custom} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, custom: e.target.value } })} />
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        )
                                    })}
                                </div>
                            </div >

                            {/* Activity Stream (Refinement: Taller & Copy) */}
                            < div className="flex-1 bg-slate-950 rounded-[2.5rem] border border-slate-800 p-6 relative overflow-hidden flex flex-col shadow-2xl min-h-0" >
                                <div className="flex justify-between items-center mb-4 pb-4 border-b border-white/5">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Live Uplink</span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <span className="text-[9px] font-mono text-slate-600">ID: {Math.random().toString(36).substr(2, 6).toUpperCase()}</span>
                                        <button onClick={copyLogs} className="text-slate-500 hover:text-indigo-400 transition-colors">
                                            <Copy className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto space-y-3 font-mono text-[10px] custom-scrollbar text-slate-400 pb-2">
                                    {logs.length === 0 && <div className="text-center mt-10 opacity-30">Awaiting Signal...</div>}
                                    {logs.map((log, i) => (
                                        <div key={i} className="animate-in fade-in slide-in-from-left-2 break-words">
                                            <span className="text-indigo-500 mr-2 opacity-50">&gt;</span>
                                            {log}
                                        </div>
                                    ))}
                                </div>
                            </div >

                        </div >

                        {/* Launch Action Bar (Bottom - Fixed) */}
                        < div className="col-span-12 row-start-2 mt-4 pt-4 border-t border-slate-200/50" >
                            <button
                                onClick={handleLaunch}
                                disabled={status === 'RUNNING'}
                                className={`w-full py-6 rounded-[2rem] font-black text-xl tracking-tight transition-all flex items-center justify-center gap-4 shadow-xl ${status === 'RUNNING' ? 'bg-slate-100 text-slate-300 cursor-not-allowed' : 'bg-indigo-600 text-white hover:bg-indigo-500 hover:scale-[1.01] active:scale-95 shadow-indigo-500/30'}`}
                            >
                                {status === 'RUNNING' ? <Cpu className="w-6 h-6 animate-spin" /> : <Zap className="w-6 h-6 fill-amber-300 text-amber-300" />}
                                {status === 'RUNNING' ? 'MISSION IN PROGRESS...' : 'LAUNCH RESEARCH PIPELINE'}
                            </button>
                        </div >
                    </div >

                    {/* === OUTPUT TAB === */}
                    < div className={`absolute inset-0 p-8 flex flex-col gap-6 transition-all duration-500 transform ${activeTab === 'OUTPUT' ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0 pointer-events-none'}`}>

                        {/* Output Sub-Nav */}
                        < div className="flex justify-between items-center" >
                            <div className="flex gap-2">
                                {['SYNTHESIS', 'RAW', 'SOURCE', 'OUTPUT'].map(view => (
                                    <button
                                        key={view}
                                        onClick={() => setOutputView(view)}
                                        className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${outputView === view ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200' : 'bg-white text-slate-400 hover:bg-slate-50'}`}
                                    >
                                        {view}
                                    </button>
                                ))}
                            </div>
                            <div className="text-xs font-bold text-slate-400">Mission Artifacts</div>
                        </div >

                        {/* Content Area */}
                        < div className="flex-1 bg-white rounded-[2.5rem] border border-slate-200 shadow-sm p-8 flex flex-col items-center justify-center text-center" >
                            {outputView === 'SYNTHESIS' && (
                                <div className="space-y-6 w-full">
                                    {status === 'COMPLETED' || status === 'RUNNING' ? (
                                        <div className="space-y-6">
                                            {/* Summary Info */}
                                            <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100 text-left">
                                                <div className="text-xs font-black text-indigo-700 uppercase mb-2">Current Mission</div>
                                                <div className="text-sm text-slate-700">
                                                    <span className="font-bold">Topic:</span> {context.topic || 'N/A'} |{' '}
                                                    <span className="font-bold">Grade:</span> {context.grade || 'General'} |{' '}
                                                    <span className="font-bold">Difficulty:</span> {context.difficulty || 'Connect'}
                                                </div>
                                            </div>
                                            {/* Output Cards */}
                                            <div className="grid grid-cols-3 gap-6">
                                                {[
                                                    { name: 'Quiz', enabled: context.outputs?.quiz },
                                                    { name: 'Study Guide', enabled: context.outputs?.studyGuide },
                                                    { name: 'Handout', enabled: context.outputs?.handout }
                                                ].map((item) => (
                                                    <div
                                                        key={item.name}
                                                        onClick={() => item.enabled && status === 'COMPLETED' && handleOpenFolder('outputs/final')}
                                                        className={`p-6 rounded-[2rem] border transition-all ${item.enabled
                                                            ? status === 'COMPLETED'
                                                                ? 'bg-emerald-50 border-emerald-200 cursor-pointer hover:border-emerald-400'
                                                                : 'bg-amber-50 border-amber-200'
                                                            : 'bg-slate-50 border-slate-100 opacity-40'
                                                            }`}
                                                    >
                                                        <div className={`w-12 h-12 rounded-xl shadow-sm flex items-center justify-center mb-4 mx-auto ${item.enabled
                                                            ? status === 'COMPLETED' ? 'bg-emerald-500' : 'bg-amber-500'
                                                            : 'bg-slate-200'
                                                            }`}>
                                                            <FileText className={`w-6 h-6 ${item.enabled ? 'text-white' : 'text-slate-400'}`} />
                                                        </div>
                                                        <div className={`text-xs font-black uppercase ${item.enabled ? 'text-slate-800' : 'text-slate-400'}`}>{item.name}</div>
                                                        <div className={`text-[9px] font-bold mt-1 ${item.enabled
                                                            ? status === 'COMPLETED' ? 'text-emerald-600' : 'text-amber-600'
                                                            : 'text-slate-300'
                                                            }`}>
                                                            {item.enabled ? (status === 'COMPLETED' ? '✓ Ready' : 'Generating...') : 'Disabled'}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="opacity-40 space-y-4">
                                            <Layers className="w-16 h-16 text-slate-300 mx-auto" />
                                            <div className="text-sm font-black text-slate-300 uppercase tracking-widest">No Synthesis Data Available</div>
                                            <div className="text-xs text-slate-400">Run a mission to generate outputs</div>
                                        </div>
                                    )}
                                </div>
                            )}
                            {
                                outputView === 'RAW' && (
                                    <div className="w-full h-full p-4 bg-slate-50 rounded-[2rem] font-mono text-[10px] text-slate-600 overflow-auto text-left">
                                        <pre>{JSON.stringify({ context, config, status }, null, 2)}</pre>
                                    </div>
                                )
                            }
                            {
                                outputView === 'SOURCE' && (
                                    <div className="w-full h-full text-left space-y-4 overflow-auto">
                                        <h3 className="text-xs font-black uppercase tracking-widest text-slate-500">Configured Sources</h3>

                                        {/* Target URLs */}
                                        {context.targetUrls && (
                                            <div className="p-4 bg-indigo-50 rounded-2xl border border-indigo-100">
                                                <div className="text-[10px] font-black text-indigo-600 uppercase mb-2">Target URLs</div>
                                                <div className="space-y-1">
                                                    {context.targetUrls.split(',').map((url, i) => (
                                                        <div key={i} className="flex items-center gap-2 text-xs text-slate-700">
                                                            <LinkIcon className="w-3 h-3 text-indigo-400" />
                                                            <span className="truncate">{url.trim()}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Local File */}
                                        {context.localFilePath && (
                                            <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
                                                <div className="text-[10px] font-black text-emerald-600 uppercase mb-2">Local File</div>
                                                <div className="flex items-center gap-2 text-xs text-slate-700">
                                                    <Folder className="w-3 h-3 text-emerald-400" />
                                                    <span>{context.localFilePath}</span>
                                                </div>
                                            </div>
                                        )}

                                        {/* Web Search Info */}
                                        {context.searchWeb && (
                                            <div className="p-4 bg-amber-50 rounded-2xl border border-amber-100">
                                                <div className="text-[10px] font-black text-amber-600 uppercase mb-2">Web Search Mode</div>
                                                <div className="text-xs text-slate-700 space-y-1">
                                                    <div><span className="font-bold">Topic:</span> {context.topic}</div>
                                                    <div><span className="font-bold">Grade:</span> {context.grade}</div>
                                                    <div><span className="font-bold">Subject:</span> {context.subject}</div>
                                                    {context.subtopics && <div><span className="font-bold">Subtopics:</span> {context.subtopics}</div>}
                                                </div>
                                            </div>
                                        )}

                                        {/* Intelligence Source */}
                                        <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100">
                                            <div className="text-[10px] font-black text-slate-500 uppercase mb-2">Intelligence Source</div>
                                            <div className="flex items-center gap-2 text-xs text-slate-700">
                                                <Bot className="w-3 h-3 text-slate-400" />
                                                <span className="font-bold">{context.intelligenceSource || 'NOTEBOOKLM'}</span>
                                            </div>
                                        </div>

                                        {/* Empty State */}
                                        {!context.targetUrls && !context.localFilePath && !context.searchWeb && (
                                            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-100 text-center">
                                                <span className="text-xs text-slate-400 italic">No sources configured. Add URLs or enable Web Search.</span>
                                            </div>
                                        )}
                                    </div>
                                )
                            }
                            {
                                outputView === 'OUTPUT' && (
                                    <div className="space-y-4">
                                        <div className="p-6 bg-slate-50 rounded-[2rem] border border-slate-200 w-96">
                                            <Folder className="w-10 h-10 text-indigo-300 mx-auto mb-4" />
                                            <h3 className="text-sm font-black text-slate-700 uppercase mb-4">Local Artifacts</h3>
                                            <div className="space-y-2">
                                                <button
                                                    onClick={() => handleOpenFolder('outputs/html/cleaned')}
                                                    className="w-full py-3 bg-white border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest hover:border-indigo-400 hover:text-indigo-600 transition-all"
                                                >
                                                    Open Raw HTML Folder
                                                </button>
                                                <button
                                                    onClick={() => handleOpenFolder('outputs/final')}
                                                    className="w-full py-3 bg-white border border-slate-200 rounded-xl text-[10px] font-black uppercase tracking-widest hover:border-indigo-400 hover:text-indigo-600 transition-all"
                                                >
                                                    Open Generated PDFs
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                )
                            }
                        </div >
                    </div >

                </div >
            </div >
        </div >
    );
};

export default AutoMode;

