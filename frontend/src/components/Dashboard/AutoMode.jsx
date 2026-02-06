import React, { useState, useEffect } from 'react';
import { Play, ShieldCheck, Activity, Terminal, Globe, Bot, Download, Check, Link as LinkIcon, Search, Layers, FileText, Cpu, Zap, AlertCircle, AlertTriangle, CheckCircle, BookOpen, HelpCircle, Layout, ClipboardList, Folder, ChevronRight, X, Copy, StickyNote, Clipboard, Loader2, Sparkles, ArrowRight, ExternalLink } from 'lucide-react';
import { logGate } from '../../services/loggingService';
import { useBackendStatus } from '../../hooks/useBackendStatus';
import { API_BASE_URL } from '../../services/apiConfig';

// --- Query Builder Logic (Report Implementation) ---
const buildEducationalQuery = (context, config) => {
    if (context.targetUrls && !context.searchWeb) {
        return `Please analyze the following URLs:\n${context.targetUrls}`;
    }

    const parts = [];

    // 1. Grade Constraint (High Priority)
    if (context.grade) {
        parts.push(`"Grade ${context.grade}"`);
    }

    // 2. Subject (High Priority)
    if (context.subject) {
        parts.push(context.subject);
    }

    // 3. Topic (Medium Priority, quoted if multi-word)
    if (context.topic) {
        const topic = context.topic.includes(' ') ? `"${context.topic}"` : context.topic;
        parts.push(topic);
    }

    // 4. Subtopics (Medium Priority) - Adding as keywords
    if (context.subtopics) {
        // Simple heuristic: just add them. If multi-word, maybe quote?
        // For now, keep it simple to avoid over-constraining.
        parts.push(context.subtopics);
    }

    // 5. Content Type Terms (Contextual)
    const contentTerms = [];
    if (context.outputs?.studyGuide) contentTerms.push('concept', 'explanation', 'reasoning');
    if (context.outputs?.handout) contentTerms.push('diagram', 'flowchart', 'infographic');
    if (context.outputs?.quiz) contentTerms.push('worksheet', 'exercise', 'practice');

    // Default to concept if nothing selected or just general search
    if (contentTerms.length === 0) contentTerms.push('concept', 'explanation');

    // Deduplicate
    const uniqueTerms = [...new Set(contentTerms)];
    if (uniqueTerms.length > 0) {
        parts.push(`(${uniqueTerms.join(' OR ')})`);
    }

    // 6. Trusted Sites (Optional restriction)
    if (context.useTrustedSites && config.trustedDomains) {
        const sites = config.trustedDomains.split(',').map(s => s.trim()).filter(s => s);
        if (sites.length > 0) {
            const siteClauses = sites.map(s => `site:${s}`);
            parts.push(`(${siteClauses.join(' OR ')})`);
        }
    }

    // 7. Scrape Keywords (Extra)
    if (context.keywordsScrape) {
        parts.push(context.keywordsScrape);
    }

    return parts.join(' ');
};

// --- Guided Mode Popup Component ---
const GuidedModePopup = ({ isOpen, onClose, context, config, onUpdateContext }) => {
    const [logs, setLogs] = useState([]);
    const [copiedOutput, setCopiedOutput] = useState(false);
    const [outputPromptText, setOutputPromptText] = useState('');
    const [inputPromptText, setInputPromptText] = useState('');
    const [pastedResults, setPastedResults] = useState('');

    const handlePasteResults = (e) => {
        const text = e.target.value;
        setPastedResults(text);

        // Extract URLs
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const matches = text.match(urlRegex);
        if (matches && matches.length > 0 && onUpdateContext) {
             const uniqueUrls = [...new Set(matches)];
             // Update targetUrls in context (replacing existing to avoid duplicates/confusion)
             onUpdateContext(prev => ({ ...prev, targetUrls: uniqueUrls.join('\n') }));
        }
    };

    // Initialize/Update prompts when context/config changes
    useEffect(() => {
        if (isOpen) {
            setInputPromptText(buildEducationalQuery(context, config));
        }
    }, [isOpen, context, config]);

    const generateOutputPrompt = () => {
        const sections = [];
        const header = [];
        header.push(`# OUTPUT GENERATION FOR: ${context.topic || 'Analysis'}`);
        header.push(`Target Audience: Grade ${context.grade || 'General'} ${context.subject || ''}`);
        const diffMap = {
            'Identify': 'Focus on definitions, basic facts, and identification of key terms. (Easy Level)',
            'Connect': 'Focus on relationships, cause-and-effect, and connecting concepts. (Medium Level)',
            'Extend': 'Focus on applications, scenario-based analysis, and extending concepts. (Hard Level)'
        };
        header.push(`[DIFFICULTY: ${context.difficulty || 'Connect'}] ${diffMap[context.difficulty] || diffMap['Connect']}`);
        if (context.keywordsReport) header.push(`[FOCUS KEYWORDS]: ${context.keywordsReport}`);
        sections.push(header.join('\n'));

        // SOURCE CONTEXT (From Search Results)
        if (context.targetUrls) {
             const sourceSec = [];
             sourceSec.push(`### SOURCE CONTEXT`);
             sourceSec.push(`Please use the following sources for your analysis:`);
             sourceSec.push(context.targetUrls);
             sections.push(sourceSec.join('\n'));
        }

        const csvTask = [];
        csvTask.push(`### PART 1: DATA EXPORT (CSV FORMAT)`);
        csvTask.push(`Generate a raw CSV code block containing the key facts, questions, and data points from the sources.`);
        csvTask.push(`CRITICAL: Use a valid CSV structure (comma separated, quotes for escaping). No conversational text inside this section.`);
        sections.push(csvTask.join('\n'));

        const studyTask = [];
        studyTask.push(`### PART 2: STUDY MATERIAL (WORD/MARKDOWN FORMAT)`);
        if (context.outputs?.studyGuide) studyTask.push(`- **Study Guide**: Create a detailed study guide with Anchor Concepts, key definitions, and detailed explanations.`);
        if (context.outputs?.quiz) {
            const q = context.quizConfig || {};
            studyTask.push(`- **Quiz**: Create a quiz with ${q.mcq || 10} MCQs, ${q.ar || 5} Assertion-Reasoning, and ${q.detailed || 3} Detailed Answer questions. Include a separate Answer Key.`);
        }
        if (context.outputs?.handout) studyTask.push(`- **Handout**: Create a Visual Handout script with a one-page summary and descriptions for relevant diagrams.`);
        if (context.quizConfig?.custom) studyTask.push(`- **Additional Instructions**: ${context.quizConfig.custom}`);
        sections.push(studyTask.join('\n'));

        const finalInstructions = [];
        finalInstructions.push(`### GENERATION RULES:`);
        finalInstructions.push(`1. Provide BOTH the CSV block and the Study Material in the same response.`);
        finalInstructions.push(`2. Keep sections clearly separated.`);
        finalInstructions.push(`3. Ensure all content is educationally sound and matches the specified difficulty.`);
        sections.push(finalInstructions.join('\n'));

        return sections.join('\n\n---\n\n');
    };

    const copyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setCopiedOutput(true);
        setTimeout(() => setCopiedOutput(false), 2000);
    };

    const outputPrompt = generateOutputPrompt();

    useEffect(() => {
        setOutputPromptText(outputPrompt);
    }, [outputPrompt]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-[2rem] w-full max-w-3xl max-h-[85vh] overflow-hidden shadow-2xl border border-zinc-200">
                <div className="flex items-center justify-between p-6 border-b border-zinc-100 bg-zinc-50/50">
                    <div className="flex items-center gap-4">
                        <div className="p-3 bg-violet-100 rounded-xl text-violet-600">
                            <Bot className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-zinc-800">Static Mode Generator</h2>
                            <p className="text-sm text-zinc-500">Manual orchestration helper (Offline/GitHub Pages)</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-zinc-100 rounded-full transition-colors">
                        <X className="w-5 h-5 text-zinc-400" />
                    </button>
                </div>

                <div className="p-8 space-y-8 overflow-y-auto max-h-[60vh] custom-scrollbar">
                    <div className="space-y-3">
                        <div className="flex justify-between items-center pl-1">
                            <label className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                                Step 1: Input Source Context (Search Query)
                            </label>
                            {context.searchWeb && (
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => {
                                            const url = context.intelligenceSource === 'DDG'
                                                ? `https://duckduckgo.com/?q=${encodeURIComponent(inputPromptText)}`
                                                : `https://www.google.com/search?q=${encodeURIComponent(inputPromptText)}`;
                                            window.open(url, '_blank');
                                        }}
                                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                                            context.intelligenceSource === 'DDG'
                                            ? 'bg-orange-50 text-orange-600 hover:bg-orange-100'
                                            : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
                                        }`}
                                    >
                                        {context.intelligenceSource === 'DDG' ? <Search className="w-3 h-3" /> : <Globe className="w-3 h-3" />}
                                        {context.intelligenceSource === 'DDG' ? 'Open DuckDuckGo' : 'Open Google Search'}
                                    </button>
                                    {context.intelligenceSource === 'DDG' && (
                                        <button
                                            onClick={() => window.open(`https://duckduckgo.com/?q=${encodeURIComponent(inputPromptText)}&ia=chat`, '_blank')}
                                            className="flex items-center gap-2 px-3 py-1.5 bg-violet-50 text-violet-600 hover:bg-violet-100 rounded-lg text-xs font-bold transition-all"
                                        >
                                            <Sparkles className="w-3 h-3" />
                                            Ask Duck.ai
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                        <div className="relative group">
                            <textarea
                                value={inputPromptText}
                                onChange={(e) => setInputPromptText(e.target.value)}
                                className="w-full h-32 p-4 bg-white border-2 border-violet-100 rounded-xl text-sm font-mono text-zinc-700 resize-none focus:outline-none focus:border-violet-500 shadow-sm"
                            />
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="flex justify-between items-center pl-1">
                            <label className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                                Step 1.5: Paste Search Results
                            </label>
                             <div className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">
                                Auto-extracts URLs
                            </div>
                        </div>
                        <textarea
                            value={pastedResults}
                            onChange={handlePasteResults}
                            placeholder="Paste Google Search results here (Ctrl+V)..."
                            className="w-full h-24 p-4 bg-white border-2 border-violet-100 rounded-xl text-sm font-mono text-zinc-700 resize-none focus:outline-none focus:border-violet-500 shadow-sm placeholder:text-zinc-300"
                        />
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center justify-between pl-1">
                            <label className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                                Step 2: Output Prompt (For AI Model)
                            </label>
                            <button
                                onClick={() => copyToClipboard(outputPromptText)}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${copiedOutput
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-zinc-100 text-zinc-600 hover:bg-violet-100 hover:text-violet-700'
                                    }`}
                            >
                                {copiedOutput ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                                {copiedOutput ? 'Copied!' : 'Copy to Clipboard'}
                            </button>
                        </div>
                        <textarea
                            value={outputPromptText}
                            onChange={(e) => setOutputPromptText(e.target.value)}
                            className="w-full h-48 p-4 bg-white border-2 border-violet-100 rounded-xl text-sm font-mono text-zinc-700 resize-y focus:outline-none focus:border-violet-500 shadow-sm"
                            placeholder="Edit prompt..."
                        />
                    </div>
                </div>

                <div className="p-6 border-t border-zinc-100 bg-zinc-50 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-8 py-3 bg-zinc-900 text-white rounded-xl text-sm font-bold hover:bg-zinc-800 transition-all shadow-lg shadow-zinc-200"
                    >
                        Done
                    </button>
                </div>
            </div>
        </div>
    );
};

// --- Sub-components ---

const TabButton = ({ label, active, onClick, icon }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-2 px-6 py-3 rounded-full transition-all duration-300 font-bold text-xs uppercase tracking-widest ${
            active
                ? 'bg-zinc-900 text-white shadow-lg shadow-zinc-200 scale-105'
                : 'bg-transparent text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600'
        }`}
    >
        {icon}
        <span>{label}</span>
    </button>
);

const InputField = ({ label, value, onChange, placeholder, type = "text", required = false, error, disabled = false }) => (
    <div className={`space-y-2 ${disabled ? 'opacity-40 pointer-events-none' : ''}`}>
        <div className="flex justify-between items-center pl-1">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                {label} {required && <span className="text-violet-500">*</span>}
            </label>
            {error && <span className="text-[10px] font-bold text-rose-500 flex items-center gap-1"><AlertCircle className="w-3 h-3" /> {error}</span>}
        </div>
        <div className="relative group">
            <input
                type={type}
                className={`w-full px-4 py-3 bg-white border ${error ? 'border-rose-200 focus:border-rose-400' : 'border-zinc-200 focus:border-violet-500'} rounded-xl outline-none font-medium text-zinc-700 text-sm shadow-sm transition-all focus:ring-4 focus:ring-violet-50 placeholder:text-zinc-300`}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                disabled={disabled}
            />
            {value && !error && !disabled && (
                <div className="absolute right-3 top-3.5 text-emerald-500 animate-in zoom-in duration-300">
                    <CheckCircle className="w-4 h-4" />
                </div>
            )}
        </div>
    </div>
);

const TextAreaField = ({ label, value, onChange, placeholder, required = false, error, disabled = false, rows = 3 }) => (
    <div className={`space-y-2 ${disabled ? 'opacity-40 pointer-events-none' : ''}`}>
        <div className="flex justify-between items-center pl-1">
            <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                {label} {required && <span className="text-violet-500">*</span>}
            </label>
            {error && <span className="text-[10px] font-bold text-rose-500 flex items-center gap-1"><AlertCircle className="w-3 h-3" /> {error}</span>}
        </div>
        <div className="relative group">
            <textarea
                rows={rows}
                className={`w-full px-4 py-3 bg-white border ${error ? 'border-rose-200 focus:border-rose-400' : 'border-zinc-200 focus:border-violet-500'} rounded-xl outline-none font-medium text-zinc-700 text-sm shadow-sm transition-all focus:ring-4 focus:ring-violet-50 placeholder:text-zinc-300 resize-y`}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                disabled={disabled}
            />
        </div>
    </div>
);

// --- Modern Intelligence Source Selector ---
const IntelligenceSourceSelector = ({ value, onChange, config, searchWeb, onToggleSearch, isOffline, useTrustedSites, onToggleTrustedSites, onFetch, isFetching }) => {
    const crawlersDisabled = searchWeb || isOffline; // Disable crawlers if offline
    const fetchersDisabled = !searchWeb;

    const SourceButton = ({ id, label, icon: Icon, disabled, subText }) => (
        <button
            onClick={() => !disabled && onChange(id)}
            disabled={disabled}
            className={`flex flex-col items-center justify-center p-4 rounded-xl transition-all relative border ${
                value === id
                    ? 'bg-zinc-800 border-zinc-700 text-white shadow-lg shadow-zinc-200 scale-[1.02]'
                    : disabled
                        ? 'bg-zinc-50 border-zinc-100 text-zinc-300 cursor-not-allowed'
                        : 'bg-white border-zinc-200 text-zinc-500 hover:border-zinc-300 hover:bg-zinc-50'
            }`}
        >
            {Icon && <Icon className={`w-5 h-5 mb-2 ${value === id ? 'text-violet-400' : 'text-current'}`} />}
            <div className="text-[10px] font-bold uppercase tracking-widest">{label}</div>
            {subText && <div className="text-[8px] font-bold text-emerald-400 mt-1">{subText}</div>}
            {value === id && (
                <div className="absolute top-2 right-2 w-1.5 h-1.5 bg-violet-500 rounded-full animate-pulse" />
            )}
        </button>
    );

    return (
        <div className="bg-white p-6 rounded-[2rem] border border-zinc-200 shadow-sm space-y-5 mb-6">
            <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-violet-100 text-violet-600 rounded-lg">
                        <Bot className="w-4 h-4" />
                    </div>
                    <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Intelligence Source</h3>
                </div>

                <div className="flex gap-4">
                    <div className="flex items-center gap-3 bg-zinc-100 p-1 rounded-full border border-zinc-200">
                        <span className={`px-3 text-[9px] font-bold uppercase tracking-widest transition-colors ${searchWeb ? 'text-zinc-800' : 'text-zinc-400'}`}>Search Web</span>
                        <button
                            onClick={onToggleSearch}
                            className={`h-6 w-10 rounded-full relative transition-all duration-300 ${searchWeb ? 'bg-violet-600' : 'bg-zinc-300'}`}
                        >
                            <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all duration-300 ${searchWeb ? 'left-[22px]' : 'left-1'}`} />
                        </button>
                    </div>

                    {searchWeb && (
                        <div className="flex items-center gap-3 bg-zinc-100 p-1 rounded-full border border-zinc-200 animate-in fade-in slide-in-from-left-2">
                            <span className={`px-3 text-[9px] font-bold uppercase tracking-widest transition-colors ${useTrustedSites ? 'text-zinc-800' : 'text-zinc-400'}`}>Trusted Sites</span>
                            <button
                                onClick={onToggleTrustedSites}
                                className={`h-6 w-10 rounded-full relative transition-all duration-300 ${useTrustedSites ? 'bg-emerald-500' : 'bg-zinc-300'}`}
                            >
                                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-all duration-300 ${useTrustedSites ? 'left-[22px]' : 'left-1'}`} />
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className={`space-y-3 p-3 rounded-2xl bg-zinc-50/50 border border-dashed border-zinc-200 ${crawlersDisabled ? 'opacity-40 grayscale' : ''}`}>
                    <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest text-center">AI Crawlers {isOffline ? '(Offline)' : ''}</div>
                    <div className="grid grid-cols-1 gap-2">
                        <SourceButton
                            id="AUTO"
                            label="AUTO"
                            disabled={crawlersDisabled}
                            subText={config.deepseekAvailable ? "DeepSeek Enhanced" : null}
                            icon={Sparkles}
                        />
                        {(config.notebooklmAvailable || config.notebooklmGuided) && (
                            <SourceButton
                                id="NOTEBOOKLM"
                                label="NOTEBOOKLM"
                                icon={Bot}
                                disabled={crawlersDisabled}
                                subText={config.notebooklmGuided ? "Guided Mode" : null}
                            />
                        )}
                    </div>
                </div>

                <div className={`space-y-3 p-3 rounded-2xl bg-zinc-50/50 border border-dashed border-zinc-200 ${fetchersDisabled ? 'opacity-40 grayscale' : ''}`}>
                    <div className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest text-center">URL Fetchers</div>
                    <div className="grid grid-cols-1 gap-2">
                        <SourceButton
                            id="GOOGLE"
                            label="GOOGLE"
                            disabled={fetchersDisabled}
                            icon={Globe}
                        />
                        <SourceButton
                            id="DDG"
                            label="DUCKDUCKGO"
                            disabled={fetchersDisabled}
                            icon={Search}
                        />
                        {searchWeb && value === 'DDG' && (
                            <button
                                onClick={onFetch}
                                disabled={isFetching}
                                className="w-full mt-2 px-3 py-2 bg-orange-100 text-orange-700 hover:bg-orange-200 rounded-lg text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-sm animate-in fade-in slide-in-from-top-1"
                            >
                                {isFetching ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                                {isFetching ? 'Fetching...' : 'Fetch URLs'}
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

const LogicDifficultySelector = ({ value, onChange }) => {
    const levels = ['Identify', 'Connect', 'Extend'];
    const descriptions = {
        'Identify': 'Foundational',
        'Connect': 'Relational',
        'Extend': 'Applied'
    };

    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-zinc-200">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-zinc-400" />
                    <h3 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Logic Difficulty</h3>
                </div>
                <div className="text-[8px] font-bold text-violet-500 bg-violet-50 px-2 py-1 rounded-md uppercase tracking-wider">
                    Signal Tuning
                </div>
            </div>

            <div className="relative px-4 pb-2">
                <div className="absolute top-[14px] left-6 right-6 h-0.5 bg-zinc-100 -z-0" />
                <div className="flex justify-between relative z-10">
                    {levels.map((level, idx) => {
                        const isActive = value === level;
                        return (
                            <div key={level} className="flex flex-col items-center gap-3 cursor-pointer group" onClick={() => onChange(level)}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center border-4 transition-all duration-300 ${
                                    isActive
                                        ? 'bg-violet-600 border-violet-100 text-white shadow-lg shadow-violet-200 scale-110'
                                        : 'bg-white border-zinc-100 text-zinc-300 hover:border-violet-100'
                                }`}>
                                    <div className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-white' : 'bg-transparent'}`} />
                                </div>
                                <div className="text-center">
                                    <div className={`text-[9px] font-bold uppercase tracking-widest transition-colors ${isActive ? 'text-zinc-800' : 'text-zinc-300'}`}>
                                        {level}
                                    </div>
                                    <div className={`text-[8px] font-bold mt-0.5 transition-all ${isActive ? 'text-violet-500 opacity-100' : 'text-zinc-300 opacity-0 -translate-y-1'}`}>
                                        {descriptions[level]}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

// --- New Component: Running State Monitor ---
const MissionMonitor = ({ status, progress, logs, progressLabel }) => {
    // console.log("MissionMonitor Render: status=", status);
    return (
        <div className="absolute inset-0 bg-zinc-900 z-40 flex flex-col items-center justify-center text-white animate-in fade-in duration-500">
            {/* Background Effects */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-violet-900/20 via-zinc-900 to-zinc-950" />

            {/* Main Center Display */}
            <div className="relative z-10 flex flex-col items-center gap-8 w-full max-w-2xl px-8">
                {/* Progress Circle */}
                <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="#27272a" strokeWidth="2" />
                        <circle
                            cx="50" cy="50" r="45" fill="none" stroke="#8b5cf6" strokeWidth="2"
                            strokeDasharray={`${progress * 2.83}, 283`}
                            strokeLinecap="round"
                            className="transition-all duration-700 ease-out"
                        />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                        <span className="text-4xl font-black tracking-tighter">{progress}%</span>
                        <span className="text-[10px] uppercase tracking-widest text-zinc-500 mt-1">Completion</span>
                    </div>
                    {/* Orbiting Particles */}
                    <div className="absolute inset-0 animate-spin-slow">
                        <div className="w-2 h-2 bg-violet-400 rounded-full absolute top-0 left-1/2 -translate-x-1/2 shadow-[0_0_10px_rgba(167,139,250,0.8)]" />
                    </div>
                </div>

                {/* Status Text */}
                <div className="text-center space-y-2">
                    <h2 className={`text-2xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r ${
                        status === 'FAILED' ? 'from-red-400 to-rose-600' : 'from-white to-zinc-400'
                    }`}>
                        {status === 'RUNNING' ? 'Mission In Progress' : status === 'FAILED' ? 'Mission Failed' : 'System Standby'}
                    </h2>
                    <p className={`text-xs font-mono uppercase tracking-widest px-4 py-1.5 rounded-full inline-block ${
                        status === 'FAILED'
                            ? 'bg-red-900/20 text-red-400 border border-red-900/50'
                            : 'bg-violet-900/20 text-violet-300/80 border border-transparent'
                    }`}>
                        {progressLabel || 'INITIALIZING_SEQUENCE'}
                    </p>
                </div>

                {/* Terminal Log View */}
                <div className="w-full h-48 bg-black/50 backdrop-blur-md rounded-xl border border-white/10 p-4 font-mono text-[10px] text-zinc-400 overflow-hidden flex flex-col relative">
                    <div className="absolute top-2 right-2 flex gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-red-500/50" />
                        <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
                        <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
                    </div>
                    <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1.5 mt-2">
                        {logs.slice(0).reverse().map((log, i) => {
                            const isObj = typeof log === 'object';
                            const text = isObj ? log.text : log;
                            const level = isObj ? log.level : (text.includes('ERROR') ? 'ERROR' : 'INFO');

                            let colorClass = 'text-zinc-300';
                            if (level === 'ERROR' || text.includes('ERROR') || text.includes('CRITICAL')) colorClass = 'text-red-400 font-bold';
                            else if (level === 'WARN') colorClass = 'text-amber-400';
                            else if (level === 'GATE') colorClass = 'text-blue-300';

                            return (
                                <div key={i} className="break-words animate-in slide-in-from-left-2 flex gap-2">
                                    <span className="text-violet-500 shrink-0">➜</span>
                                    <span className={colorClass}>{text}</span>
                                </div>
                            );
                        })}
                    </div>
                    <div className="h-4 bg-gradient-to-t from-black/50 to-transparent absolute bottom-0 left-0 right-0 pointer-events-none" />
                </div>
            </div>
        </div>
    );
};

// --- Main Component ---

const AutoMode = () => {
    const { isOnline } = useBackendStatus();
    const isOffline = isOnline === false;

    // Top-Level State
    const [activeTab, setActiveTab] = useState('INPUT'); // 'INPUT' | 'OUTPUT'
    const [status, setStatus] = useState('IDLE'); // 'IDLE' | 'RUNNING' | 'COMPLETED' | 'FAILED'
    // console.log("AutoMode Render: status=", status);
    const [progress, setProgress] = useState(0);
    const [progressLabel, setProgressLabel] = useState('SYSTEM READY');
    const [results, setResults] = useState(null);
    const [showGuidedPopup, setShowGuidedPopup] = useState(false);
    const [logs, setLogs] = useState([]);
    const [isFetching, setIsFetching] = useState(false);

    const [outputView, setOutputView] = useState('SYNTHESIS');

    const [context, setContext] = useState({
        searchWeb: false,
        targetUrls: '',
        grade: '',
        subject: '',
        topic: '',
        subtopics: '',
        intelligenceSource: 'NOTEBOOKLM',
        keywordsScrape: '',
        keywordsReport: '',
        localFilePath: '',
        outputs: { studyGuide: true, quiz: true, handout: false },
        quizConfig: { mcq: 10, ar: 5, detailed: 3, custom: '' },
        difficulty: 'Connect',
        useTrustedSites: true // Default enabled for better quality
    });

    const [errors, setErrors] = useState({});
    const [config, setConfig] = useState({
        maxTokens: 2000, strategy: 'section_aware', model: 'gpt-4-turbo', headless: false,
        chromeUserDataDir: '', discoveryMethod: 'notebooklm', notebooklmAvailable: true,
        deepseekAvailable: false, notebooklmGuided: false,
        trustedDomains: 'byjus.com, vedantu.com, khanacademy.org, ncert.nic.in, toppr.com, meritnation.com'
    });

    useEffect(() => {
        const loadConfig = async () => {
            if (!isOnline) return;
            try {
                const response = await fetch(`${API_BASE_URL}/api/config/load`);
                if (response.ok) {
                    const data = await response.json();
                    setConfig(prev => ({ ...prev, ...data }));
                }
            } catch (e) { console.log('Config load skipped'); }
        };
        if (isOnline) loadConfig();
    }, [isOnline]);

    // useEffect(() => {
    //     // If offline, default to Search Web (Fetchers) as Crawlers are server-side
    //     if (isOffline && !context.searchWeb) {
    //         setContext(prev => ({ ...prev, searchWeb: true, intelligenceSource: 'GOOGLE' }));
    //     }
    // }, [isOffline]);

    useEffect(() => {
        const savedContext = localStorage.getItem('dashboard_context');
        if (savedContext) {
            try { setContext(prev => ({ ...prev, ...JSON.parse(savedContext) })); } catch (e) {}
        }
    }, []);

    useEffect(() => { localStorage.setItem('dashboard_context', JSON.stringify(context)); }, [context]);

    useEffect(() => {
        if (context.searchWeb) {
            if (context.intelligenceSource === 'AUTO' || context.intelligenceSource === 'NOTEBOOKLM') {
                setContext(prev => ({ ...prev, intelligenceSource: 'GOOGLE' }));
            }
        } else {
            if (context.intelligenceSource === 'GOOGLE' || context.intelligenceSource === 'DDG') {
                setContext(prev => ({ ...prev, intelligenceSource: 'AUTO' }));
            }
        }
    }, [context.searchWeb]);

    const validateInput = () => {
        const newErrors = {};
        const validGrades = ['3', '4', '5', '6', '7', '8', '9'];

        if (context.searchWeb) {
            if (!context.grade) newErrors.grade = "Required";
            else if (!validGrades.includes(context.grade)) newErrors.grade = "Grade 3-9 Only";
            if (!context.subject) newErrors.subject = "Required";
            if (!context.topic) newErrors.topic = "Required";
            else if (context.topic.length < 3) newErrors.topic = "Min 3 chars";
        } else {
            if (!context.targetUrls && !context.localFilePath) {
                if (!context.localFilePath && !context.topic) newErrors.targetUrls = "Required";
            }
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const checkStatus = async () => {
        if (!isOnline) return;
        try {
            const response = await fetch(`${API_BASE_URL}/api/logs`);
            const data = await response.json();

            if (data.logs) {
                // REVAMP: Keep all logs, including ERROR/WARN, and preserve structure
                const formattedLogs = data.logs.map(l => {
                    if (typeof l === 'string') return l;
                    return {
                        text: `[${l.level || 'INFO'}] ${l.message || ''}`,
                        level: l.level,
                        message: l.message
                    };
                });
                setLogs(formattedLogs);

                const lastLogEntry = formattedLogs.length > 0 ? formattedLogs[formattedLogs.length - 1] : "";
                const lastLogText = typeof lastLogEntry === 'object' ? lastLogEntry.text : lastLogEntry;

                if (lastLogText.includes("NotebookLM")) { setProgress(30); setProgressLabel("NOTEBOOKLM_DRIVER_ACTIVE"); }
                else if (lastLogText.includes("uploaded") || lastLogText.includes("Source Discovery")) { setProgress(50); setProgressLabel("SOURCE_ACQUISITION"); }
                else if (lastLogText.includes("Chat processed") || lastLogText.includes("Report Generation")) { setProgress(70); setProgressLabel("INFERENCE_ENGINE_PROCESSING"); }
                else if (lastLogText.includes("Saved") || lastLogText.includes("Exporting report")) { setProgress(90); setProgressLabel("ARTIFACT_SERIALIZATION"); }

                if (data.status === 'COMPLETED') {
                    setStatus('COMPLETED');
                    setProgress(100);
                    setProgressLabel("MISSION_COMPLETE");
                    setResults({ timestamp: new Date(), artifacts: true });
                    setActiveTab('OUTPUT'); // Auto-switch to output
                } else if (data.status === 'FAILED') {
                    setStatus('FAILED');
                    setProgressLabel("MISSION_FAILED");
                }
            }
        } catch (e) { console.error("Polling error", e); }
    };

    useEffect(() => {
        let interval;
        if (status === 'RUNNING') interval = setInterval(checkStatus, 2000);
        return () => clearInterval(interval);
    }, [status]);

    const handleFetchUrls = async () => {
        if (!context.grade || !context.subject || !context.topic) {
             setLogs(prev => [`[VALIDATION_ERROR] Grade, Subject, and Topic are required to fetch URLs`, ...prev]);
             return;
        }

        setIsFetching(true);
        setLogs(prev => [`[SYSTEM] Fetching URLs via Bridge...`, ...prev]);

        try {
            const response = await fetch(`${API_BASE_URL}/api/discovery/fetch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    grade: context.grade,
                    subject: context.subject,
                    topic: context.topic,
                    subtopics: context.subtopics,
                    maxResults: 5,
                    trustedDomains: context.useTrustedSites ? config.trustedDomains : null
                })
            });
            const data = await response.json();

            if (data.success && data.results) {
                const urls = data.results.map(r => r.url).join('\n');
                setContext(prev => ({
                    ...prev,
                    targetUrls: urls,
                    searchWeb: false // Switch to Direct Mode
                }));
                setLogs(prev => [`[SUCCESS] Fetched ${data.results.length} URLs. Switched to Direct Mode.`, ...prev]);
            } else {
                throw new Error("No results returned");
            }
        } catch (e) {
            setLogs(prev => [`[ERROR] Fetch failed: ${e.message}`, ...prev]);
        } finally {
            setIsFetching(false);
        }
    };

    const handleOpenFolder = async (path) => {
        if (isOffline) {
            alert("File system access is unavailable in Static Mode.");
            return;
        }
        try { await fetch(`${API_BASE_URL}/api/explore?path=${encodeURIComponent(path)}`); } catch (e) {}
    };

    const handleLaunch = async () => {
        // Offline / Static Mode Intercept
        if (isOffline || config.notebooklmGuided) {
            setShowGuidedPopup(true);
            return;
        }

        if (!validateInput()) {
            setLogs(prev => [`[VALIDATION_ERROR] Check input fields`, ...prev]);
            return;
        }

        setStatus('RUNNING');
        setActiveTab('INPUT');
        setProgress(5);
        setLogs(['[SYSTEM] Initiating mission protocol...', `[CONFIG] Source: ${context.intelligenceSource}`]);

        try {
            const response = await fetch(`${API_BASE_URL}/api/auto/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    targetUrl: context.searchWeb ? '' : context.targetUrls,
                    grade: context.grade || 'General',
                    topic: context.topic || 'Analysis',
                    subtopics: context.subtopics,
                    materialType: 'mixed_outputs',
                    customPrompt: context.quizConfig.custom,
                    sourceType: context.intelligenceSource.toLowerCase(),
                    config: {
                        ...config,
                        discoveryMethod: (context.intelligenceSource === 'AUTO' || context.intelligenceSource === 'GOOGLE' || context.intelligenceSource === 'DDG')
                            ? (context.searchWeb ? 'Auto' : 'Direct')
                            : config.discoveryMethod || 'notebooklm',
                        outputs: context.outputs,
                        quizConfig: context.quizConfig,
                        difficulty: context.difficulty,
                        keywordsReport: context.keywordsReport,
                        localFilePath: context.localFilePath,
                        modes: { D: config.notebooklmAvailable }
                    }
                })
            });
            const data = await response.json();
            if (!data.success) throw new Error(data.detail || 'Execution failed');
        } catch (error) {
            setLogs(prev => [`[CRITICAL] ${error.message}`, ...prev]);
            setStatus('FAILED');
        }
    };

    return (
        <div className="flex h-[880px] bg-zinc-950 rounded-[3rem] overflow-hidden shadow-2xl border border-zinc-900 font-sans relative">

            {/* Guided Mode Popup */}
            <GuidedModePopup
                isOpen={showGuidedPopup}
                onClose={() => setShowGuidedPopup(false)}
                context={context}
                onUpdateContext={setContext}
                config={config}
            />

            {/* --- Running State Overlay (Mission Monitor) --- */}
            {(status === 'RUNNING' || status === 'FAILED') && (
                <div className="absolute inset-0 z-50">
                    <MissionMonitor
                        status={status}
                        progress={progress}
                        logs={logs}
                        progressLabel={progressLabel}
                        onClose={() => setStatus('IDLE')}
                    />
                    {status === 'FAILED' && (
                         <div className="absolute top-8 right-8 z-[60]">
                             <button
                                 onClick={() => setStatus('IDLE')}
                                 className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider shadow-lg transition-all flex items-center gap-2"
                             >
                                 <X className="w-4 h-4" />
                                 Dismiss
                             </button>
                         </div>
                    )}
                </div>
            )}

            {/* --- Sidebar --- */}
            <div className="w-20 bg-zinc-950 flex flex-col items-center py-8 z-20 border-r border-white/5">
                <div className="p-3 bg-violet-600 rounded-2xl mb-12 shadow-[0_0_20px_rgba(124,58,237,0.3)]">
                    <Activity className="w-6 h-6 text-white" />
                </div>
            </div>

            {/* --- Main Workspace --- */}
            <div className="flex-1 flex flex-col bg-zinc-50 relative overflow-hidden">

                {/* Header Navigation */}
                <div className="h-20 flex items-center justify-center px-8 bg-zinc-50 border-b border-zinc-100/50 z-20">
                    <div className="bg-zinc-100/80 backdrop-blur-md p-1.5 rounded-full flex gap-1 shadow-inner border border-zinc-200/50">
                        <TabButton
                            label="Input"
                            active={activeTab === 'INPUT'}
                            onClick={() => setActiveTab('INPUT')}
                            icon={<Search className="w-3 h-3" />}
                        />
                        <TabButton
                            label="Output"
                            active={activeTab === 'OUTPUT'}
                            onClick={() => setActiveTab('OUTPUT')}
                            icon={<Layers className="w-3 h-3" />}
                        />
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-hidden relative">

                    {/* === INPUT TAB === */}
                    <div className={`absolute inset-0 p-8 grid grid-cols-12 gap-8 transition-all duration-500 transform ${activeTab === 'INPUT' ? 'translate-x-0 opacity-100' : '-translate-x-10 opacity-0 pointer-events-none'}`}>

                        {/* LEFT COLUMN */}
                        <div className="col-span-7 h-full overflow-y-auto pr-4 custom-scrollbar pb-20">

                            <IntelligenceSourceSelector
                                value={context.intelligenceSource}
                                onChange={(val) => setContext({ ...context, intelligenceSource: val })}
                                config={config}
                                searchWeb={context.searchWeb}
                                onToggleSearch={() => setContext({ ...context, searchWeb: !context.searchWeb })}
                                isOffline={isOffline}
                                useTrustedSites={context.useTrustedSites}
                                onToggleTrustedSites={() => setContext({ ...context, useTrustedSites: !context.useTrustedSites })}
                                onFetch={handleFetchUrls}
                                isFetching={isFetching}
                            />

                            {/* Research Foundation */}
                            <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-zinc-200 space-y-6 mb-6">
                                <div className="flex items-center gap-3 border-b border-zinc-100 pb-4">
                                    <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                                        <BookOpen className="w-5 h-5" />
                                    </div>
                                    <h2 className="text-sm font-black text-zinc-700 uppercase tracking-widest">Research Context</h2>
                                </div>

                                {!context.searchWeb && (
                                    <div className="animate-in slide-in-from-top-2">
                                        <TextAreaField
                                            label="Target URLs"
                                            placeholder="Paste URLs here..."
                                            value={context.targetUrls}
                                            onChange={(e) => setContext({ ...context, targetUrls: e.target.value })}
                                            error={errors.targetUrls}
                                            rows={2}
                                        />
                                    </div>
                                )}

                                <div className={`space-y-6 transition-all duration-300 ${!context.searchWeb ? 'opacity-50' : ''}`}>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <div className="flex justify-between pl-1">
                                                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Grade</label>
                                                {errors.grade && <span className="text-[9px] text-red-500 font-bold">{errors.grade}</span>}
                                            </div>
                                            <select
                                                value={context.grade}
                                                onChange={(e) => setContext({ ...context, grade: e.target.value })}
                                                disabled={!context.searchWeb}
                                                className="w-full p-3 bg-white rounded-xl font-bold text-zinc-700 border border-zinc-200 outline-none focus:border-violet-500 focus:ring-4 focus:ring-violet-50 text-sm"
                                            >
                                                <option value="">Select Grade...</option>
                                                {[3, 4, 5, 6, 7, 8, 9].map(g => <option key={g} value={g}>Grade {g}</option>)}
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <div className="flex justify-between pl-1">
                                                <label className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">Subject</label>
                                            </div>
                                            <input
                                                list="subjects-list"
                                                value={context.subject}
                                                onChange={(e) => setContext({ ...context, subject: e.target.value })}
                                                disabled={!context.searchWeb}
                                                placeholder="Subject..."
                                                className="w-full p-3 bg-white rounded-xl font-bold text-zinc-700 border border-zinc-200 outline-none focus:border-violet-500 focus:ring-4 focus:ring-violet-50 text-sm"
                                            />
                                            <datalist id="subjects-list">
                                                {['Physics', 'Math', 'Chemistry', 'Biology', 'History', 'Geography'].map(s => <option key={s} value={s} />)}
                                            </datalist>
                                        </div>
                                    </div>

                                    <InputField
                                        label="Main Topic"
                                        placeholder="Enter topic..."
                                        value={context.topic}
                                        onChange={(e) => setContext({ ...context, topic: e.target.value })}
                                        required={context.searchWeb}
                                        error={errors.topic}
                                        disabled={!context.searchWeb && !context.localFilePath && !context.targetUrls}
                                    />

                                    <InputField
                                        label="Sub-Topics"
                                        placeholder="Specific areas..."
                                        value={context.subtopics}
                                        onChange={(e) => setContext({ ...context, subtopics: e.target.value })}
                                        disabled={!context.searchWeb}
                                    />
                                </div>
                            </div>

                            <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-zinc-200 space-y-4">
                                <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest pl-1">Advanced Config</h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <InputField label="Scrape Keywords" placeholder="Search terms..." value={context.keywordsScrape} onChange={(e) => setContext({ ...context, keywordsScrape: e.target.value })} />
                                    <InputField label="Report Keywords" placeholder="Focus terms..." value={context.keywordsReport} onChange={(e) => setContext({ ...context, keywordsReport: e.target.value })} />
                                </div>
                                <InputField label="Local File Path" placeholder="C:/Data/..." value={context.localFilePath} onChange={(e) => setContext({ ...context, localFilePath: e.target.value })} />
                            </div>
                        </div>

                        {/* RIGHT COLUMN */}
                        <div className="col-span-5 h-full flex flex-col gap-6">

                            {/* Expected Output */}
                            <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-zinc-200">
                                <div className="flex items-center gap-2 mb-4 pl-1">
                                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                                    <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Expected Artifacts</h3>
                                </div>
                                <div className="space-y-3">
                                    {['Study Guide', 'Quiz', 'Handout'].map(opt => {
                                        const key = opt.toLowerCase().replace(' ', '') === 'studyguide' ? 'studyGuide' : opt.toLowerCase().replace(' ', '');
                                        const isQuiz = key === 'quiz';
                                        return (
                                            <div key={key} className={`p-3 rounded-xl border transition-all ${context.outputs[isQuiz ? 'quiz' : key] ? 'bg-violet-50 border-violet-200' : 'bg-white border-zinc-100'}`}>
                                                <div className="flex items-center gap-3 cursor-pointer" onClick={() => setContext({ ...context, outputs: { ...context.outputs, [isQuiz ? 'quiz' : key]: !context.outputs[isQuiz ? 'quiz' : key] } })}>
                                                    <div className={`w-4 h-4 rounded border flex items-center justify-center ${context.outputs[isQuiz ? 'quiz' : key] ? 'bg-violet-600 border-violet-600' : 'bg-zinc-100 border-zinc-300'}`}>
                                                        {context.outputs[isQuiz ? 'quiz' : key] && <Check className="w-3 h-3 text-white" />}
                                                    </div>
                                                    <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-600">{opt}</span>
                                                </div>
                                                {isQuiz && context.outputs.quiz && (
                                                    <div className="mt-3 pl-7 grid grid-cols-4 gap-2">
                                                        <input type="number" className="w-full p-1.5 rounded bg-white border border-violet-100 text-[10px] font-bold text-center" value={context.quizConfig.mcq} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, mcq: e.target.value } })} />
                                                        <input type="number" className="w-full p-1.5 rounded bg-white border border-violet-100 text-[10px] font-bold text-center" value={context.quizConfig.ar} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, ar: e.target.value } })} />
                                                        <input type="number" className="w-full p-1.5 rounded bg-white border border-violet-100 text-[10px] font-bold text-center" value={context.quizConfig.detailed} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, detailed: e.target.value } })} />
                                                        <input type="text" className="w-full p-1.5 rounded bg-white border border-violet-100 text-[10px] font-bold text-center" placeholder="..." value={context.quizConfig.custom} onChange={(e) => setContext({ ...context, quizConfig: { ...context.quizConfig, custom: e.target.value } })} />
                                                    </div>
                                                )}
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>

                            <LogicDifficultySelector value={context.difficulty} onChange={(val) => setContext({ ...context, difficulty: val })} />

                            {/* Launch Button */}
                            <div className="mt-auto">
                                <button
                                    onClick={handleLaunch}
                                    className={`w-full py-5 text-white rounded-2xl font-black text-lg tracking-tight hover:scale-[1.02] active:scale-95 transition-all shadow-xl shadow-zinc-300 flex items-center justify-center gap-3 group ${isOffline ? 'bg-zinc-700 hover:bg-zinc-600' : 'bg-zinc-900 hover:bg-zinc-800'}`}
                                >
                                    <span>{isOffline ? 'GENERATE MANUAL PROMPTS' : 'INITIALIZE MISSION'}</span>
                                    <div className="p-1 bg-white/10 rounded-full group-hover:bg-white/20 transition-colors">
                                        <ArrowRight className="w-4 h-4" />
                                    </div>
                                </button>
                                {isOffline && <p className="text-[10px] text-center text-zinc-400 mt-2 uppercase tracking-widest">Static Mode Active (No Backend)</p>}
                            </div>
                        </div>
                    </div>

                    {/* === OUTPUT TAB === */}
                    <div className={`absolute inset-0 p-8 flex flex-col gap-6 transition-all duration-500 transform ${activeTab === 'OUTPUT' ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0 pointer-events-none'}`}>

                        <div className="flex justify-center mb-4">
                            <div className="bg-white p-1 rounded-xl shadow-sm border border-zinc-200 inline-flex">
                                {['SYNTHESIS', 'RAW', 'SOURCE', 'OUTPUT'].map(view => (
                                    <button
                                        key={view}
                                        onClick={() => setOutputView(view)}
                                        className={`px-5 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${outputView === view ? 'bg-zinc-900 text-white' : 'text-zinc-400 hover:text-zinc-600'}`}
                                    >
                                        {view}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="flex-1 bg-white/50 backdrop-blur-sm rounded-[2.5rem] border border-zinc-200 shadow-sm p-10 overflow-hidden relative">
                             {outputView === 'SYNTHESIS' && (
                                <div className="h-full flex flex-col items-center justify-center">
                                    {status === 'COMPLETED' ? (
                                        <div className="w-full max-w-4xl space-y-8 animate-in zoom-in duration-300">
                                            <div className="text-center space-y-2">
                                                <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-3xl mx-auto flex items-center justify-center mb-4 shadow-lg shadow-emerald-100">
                                                    <CheckCircle className="w-8 h-8" />
                                                </div>
                                                <h2 className="text-2xl font-black text-zinc-800">Mission Successful</h2>
                                                <p className="text-zinc-500 font-medium">All artifacts have been serialized and are ready for review.</p>
                                            </div>

                                            <div className="grid grid-cols-3 gap-6">
                                                {[
                                                    { name: 'Study Guide', icon: BookOpen, color: 'violet' },
                                                    { name: 'Quiz Packet', icon: HelpCircle, color: 'amber' },
                                                    { name: 'Visual Handout', icon: Layout, color: 'blue' }
                                                ].map((item) => (
                                                    <div key={item.name} className="group bg-white p-6 rounded-[2rem] border border-zinc-100 hover:border-zinc-300 shadow-sm hover:shadow-xl transition-all cursor-pointer relative overflow-hidden" onClick={() => handleOpenFolder('outputs/final')}>
                                                        <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity text-${item.color}-500`}>
                                                            <item.icon className="w-24 h-24" />
                                                        </div>
                                                        <div className={`w-12 h-12 rounded-2xl bg-${item.color}-50 text-${item.color}-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                                                            <item.icon className="w-6 h-6" />
                                                        </div>
                                                        <h3 className="text-sm font-black text-zinc-800 uppercase tracking-wide mb-1">{item.name}</h3>
                                                        <p className="text-xs text-zinc-400 font-medium">Click to open PDF</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center opacity-30">
                                            <Layers className="w-24 h-24 mx-auto mb-4 text-zinc-300" />
                                            <p className="text-lg font-black text-zinc-400 uppercase tracking-widest">No Synthesis Data</p>
                                        </div>
                                    )}
                                </div>
                             )}
                             {/* Other views (RAW, SOURCE, OUTPUT) remain similar but styled if needed. For brevity, keeping simple as user asked for 3 main screens. */}
                             {outputView !== 'SYNTHESIS' && (
                                 <div className="flex items-center justify-center h-full text-zinc-400 font-mono text-xs">
                                     View: {outputView} (Data Visualization Placeholder)
                                 </div>
                             )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default AutoMode;
