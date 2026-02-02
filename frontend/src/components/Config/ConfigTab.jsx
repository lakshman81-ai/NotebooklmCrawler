import React, { useState, useEffect } from 'react';
import { Settings, Download, Upload, Save, Clock, Globe, Bot, Cpu, Server, AlertCircle, Code, CheckCircle, Info, Zap, FolderOpen } from 'lucide-react';
import { logInfo, logError, logWarn, setWorkflow, advanceWorkflow, endWorkflow } from '../../services/loggingService';

// --- Local Storage Utilities ---
const CONFIG_STORAGE_KEY = 'orchestration_cockpit_config';

const saveToLocalStorage = (key, data) => {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (e) {
        console.error('LocalStorage save failed:', e);
        return false;
    }
};

const loadFromLocalStorage = (key) => {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (e) {
        console.error('LocalStorage load failed:', e);
        return null;
    }
};

// --- Sub-components ---

const StrategyButton = ({ label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`px-5 py-3.5 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] transition-all border-2 ${active
            ? 'bg-indigo-600 border-indigo-500 text-white shadow-xl shadow-indigo-600/20'
            : 'bg-transparent border-white/5 text-slate-500 hover:border-white/10 hover:text-slate-300'
            }`}
    >
        {label}
    </button>
);

const Toggle = ({ label, description, active, onChange, color = 'indigo' }) => {
    const colors = {
        indigo: active ? 'bg-indigo-600' : 'bg-slate-300',
        amber: active ? 'bg-amber-500' : 'bg-slate-300',
        emerald: active ? 'bg-emerald-500' : 'bg-slate-300',
    };
    return (
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-2xl border border-slate-200">
            <div>
                <div className="text-xs font-black text-slate-800 tracking-tight">{label}</div>
                {description && <div className="text-[10px] text-slate-400 font-medium uppercase tracking-tighter">{description}</div>}
            </div>
            <button
                onClick={onChange}
                className={`w-12 h-6 rounded-full relative transition-all ${colors[color]}`}
            >
                <div className={`absolute w-4 h-4 rounded-full top-1 transition-all bg-white ${active ? 'left-7 shadow-sm' : 'left-1'}`} />
            </button>
        </div>
    );
};

// --- Main Component ---

const ConfigTab = () => {
    const [config, setConfig] = useState({
        maxTokens: 1200,
        strategy: 'section_aware',
        outputType: 'study_material',
        sourceType: 'trusted',
        headless: false,
        chromeUserDataDir: '',
        discoveryMethod: 'notebooklm',
        notebooklmAvailable: true,
        deepseekAvailable: false,
        notebooklmGuided: true,
        // Domain Management
        trustedDomains: 'byjus.com, vedantu.com, khanacademy.org',
        blockedDomains: 'duckduckgo.com, youtube.com, facebook.com, twitter.com, instagram.com, pinterest.com, linkedin.com, amazon.com',
        // API Keys (Phase 4)
        geminiApiKey: '',
        openaiApiKey: '',
        deepseekApiKey: '',
        showGeminiKey: false,
        showOpenAIKey: false,
        showDeepSeekKey: false
    });

    const [saving, setSaving] = useState(false);
    const [loaded, setLoaded] = useState(false);

    // Load config from localStorage and backend on mount
    useEffect(() => {
        const loadConfig = async () => {
            logInfo('ConfigTab', 'loadConfig', 'Loading configuration...');
            // Try local storage first (fastest)
            const localConfig = loadFromLocalStorage(CONFIG_STORAGE_KEY);

            if (localConfig) {
                logInfo('ConfigTab', 'loadConfig', 'Config loaded from localStorage', { localConfig });
                setConfig(prev => ({
                    ...prev,
                    maxTokens: localConfig.maxTokens || 1200,
                    strategy: localConfig.strategy || 'section_aware',
                    outputType: localConfig.outputType || 'study_material',
                    headless: localConfig.headless || false,
                    chromeUserDataDir: localConfig.chromeUserDataDir || '',
                    discoveryMethod: localConfig.discoveryMethod || 'notebooklm',
                    notebooklmAvailable: localConfig.notebooklmAvailable !== false,
                    deepseekAvailable: localConfig.deepseekAvailable || false,
                    notebooklmGuided: localConfig.notebooklmGuided || false,
                    trustedDomains: localConfig.trustedDomains || 'byjus.com, vedantu.com, khanacademy.org',
                    blockedDomains: localConfig.blockedDomains || 'duckduckgo.com, youtube.com, facebook.com, twitter.com, instagram.com, pinterest.com, linkedin.com, amazon.com',
                    // API Keys
                    geminiApiKey: localConfig.geminiApiKey || '',
                    openaiApiKey: localConfig.openaiApiKey || '',
                    deepseekApiKey: localConfig.deepseekApiKey || ''
                }));
                setLoaded(true);
            }

            // Also try backend for newest config
            try {
                const response = await fetch('http://localhost:8000/api/config/load');
                if (response.ok) {
                    const data = await response.json();
                    logInfo('ConfigTab', 'loadConfig', 'Config loaded from backend', { backendConfig: data });
                    setConfig(prev => ({
                        ...prev,
                        maxTokens: data.maxTokens || prev.maxTokens,
                        strategy: data.strategy || prev.strategy,
                        outputType: data.outputType || prev.outputType,
                        headless: data.headless ?? prev.headless,
                        chromeUserDataDir: data.chromeUserDataDir || prev.chromeUserDataDir,
                        discoveryMethod: data.discoveryMethod || prev.discoveryMethod,
                        notebooklmAvailable: data.notebooklmAvailable ?? prev.notebooklmAvailable,
                        deepseekAvailable: data.deepseekAvailable ?? prev.deepseekAvailable,
                        notebooklmGuided: data.notebooklmGuided ?? prev.notebooklmGuided,
                        trustedDomains: data.trustedDomains || prev.trustedDomains,
                        blockedDomains: data.blockedDomains || prev.blockedDomains
                    }));
                    setLoaded(true);
                }
            } catch (e) {
                logWarn('ConfigTab', 'loadConfig', 'Backend not available, using localStorage only', { error: e.message });
            }

            if (!loaded) {
                setLoaded(true);
            }
        };
        loadConfig();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        logInfo('ConfigTab', 'handleSave', 'Saving configuration...', { config });

        const configData = {
            maxTokens: config.maxTokens,
            strategy: config.strategy,
            outputType: config.outputType,
            headless: config.headless,
            chromeUserDataDir: config.chromeUserDataDir,
            discoveryMethod: config.discoveryMethod,
            notebooklmAvailable: config.notebooklmAvailable,
            deepseekAvailable: config.deepseekAvailable,
            notebooklmGuided: config.notebooklmGuided,
            trustedDomains: config.trustedDomains,
            blockedDomains: config.blockedDomains,
            // API Keys (Phase 4)
            geminiApiKey: config.geminiApiKey,
            openaiApiKey: config.openaiApiKey,
            deepseekApiKey: config.deepseekApiKey,
            savedAt: new Date().toISOString()
        };

        // Strategy 1: Try backend first
        let backendSuccess = false;
        try {
            const response = await fetch('http://localhost:8000/api/config/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            });
            if (response.ok) {
                backendSuccess = true;
                logInfo('ConfigTab', 'handleSave', 'Config saved to backend successfully');
            }
        } catch (e) {
            logWarn('ConfigTab', 'handleSave', 'Backend not available, falling back to localStorage', { error: e.message });
        }

        // Strategy 2: Always save to local storage as backup
        const localSuccess = saveToLocalStorage(CONFIG_STORAGE_KEY, configData);

        if (backendSuccess) {
            logInfo('ConfigTab', 'handleSave', 'Settings synced to server and saved locally');
            alert('✓ Settings synced to server and saved locally');
        } else if (localSuccess) {
            logInfo('ConfigTab', 'handleSave', 'Settings saved locally (backend offline)');
            alert('✓ Settings saved locally (backend offline)');
        } else {
            logError('ConfigTab', 'handleSave', 'Save failed - storage permissions issue');
            alert('✗ Save failed - please check browser storage permissions');
        }

        setSaving(false);
    };

    console.log('[ConfigTab] Rendering with config:', config);

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-4 mb-2">
                <div className="p-3 bg-indigo-600 rounded-2xl text-white shadow-lg shadow-indigo-100">
                    <Settings className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-2xl font-black text-slate-900 tracking-tight">Technical Protocols</h2>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Pipeline Governance & Hardware Optimization</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Processing Limits */}
                <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm space-y-6">
                    <div className="flex items-center gap-2 text-indigo-600 mb-2">
                        <Cpu className="w-5 h-5" />
                        <h3 className="font-black text-sm uppercase tracking-widest">Processing Node</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block pl-1">Max Token Quota</label>
                            <input
                                type="number"
                                className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 ring-indigo-500/10 focus:border-indigo-600 outline-none transition-all font-mono font-bold text-slate-700"
                                value={config.maxTokens}
                                onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) || 0 })}
                            />
                        </div>

                        <div className="p-4 bg-amber-50 rounded-2xl border border-amber-100 flex gap-3">
                            <Info className="w-5 h-5 text-amber-600 shrink-0" />
                            <p className="text-[10px] text-amber-700 font-medium leading-relaxed">
                                Higher quotas increase synthesis depth but may impact processing latency and API costs.
                            </p>
                        </div>

                        <Toggle
                            label="Headless Execution"
                            description="Disable browser UI for performance"
                            active={config.headless}
                            onChange={() => setConfig({ ...config, headless: !config.headless })}
                        />
                    </div>
                </div>

                {/* Strategy Matrix */}
                <div className="bg-slate-900 p-8 rounded-[2.5rem] border border-slate-800 shadow-2xl space-y-6">
                    <div className="flex items-center gap-2 text-indigo-400 mb-2">
                        <Zap className="w-5 h-5" />
                        <h3 className="font-black text-sm uppercase tracking-widest text-white">Logic Strategy</h3>
                    </div>

                    <div className="space-y-6">
                        <div className="space-y-3">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block pl-1">Chunking Algorithm</label>
                            <div className="grid grid-cols-1 gap-2">
                                <StrategyButton
                                    label="SECTION AWARE"
                                    active={config.strategy === 'section_aware'}
                                    onClick={() => setConfig({ ...config, strategy: 'section_aware' })}
                                />
                                <StrategyButton
                                    label="FIXED SIZE"
                                    active={config.strategy === 'fixed_size'}
                                    onClick={() => setConfig({ ...config, strategy: 'fixed_size' })}
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block pl-1">Target Output Spec</label>
                            <select
                                className="w-full px-5 py-3 bg-slate-800 border border-slate-700 rounded-2xl text-white font-bold text-xs uppercase tracking-widest outline-none focus:border-indigo-500"
                                value={config.outputType}
                                onChange={(e) => setConfig({ ...config, outputType: e.target.value })}
                            >
                                <option value="study_material">STUDY MATERIAL (HYBRID)</option>
                                <option value="questionnaire">STRICT QUESTIONNAIRE</option>
                                <option value="handout">VISUAL HANDOUT</option>
                            </select>
                        </div>

                        <div className="space-y-3">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block pl-1">Discovery Method</label>
                            <select
                                className="w-full px-5 py-3 bg-slate-800 border border-slate-700 rounded-2xl text-white font-bold text-xs uppercase tracking-widest outline-none focus:border-indigo-500"
                                value={config.discoveryMethod}
                                onChange={(e) => setConfig({ ...config, discoveryMethod: e.target.value })}
                            >
                                <option value="notebooklm">NOTEBOOKLM</option>
                                <option value="auto">AUTO</option>
                                <option value="deepseek">DEEPSEEK</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Browser Settings */}
                <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm space-y-6">
                    <div className="flex items-center gap-2 text-indigo-600 mb-2">
                        <Globe className="w-5 h-5" />
                        <h3 className="font-black text-sm uppercase tracking-widest">Browser Settings</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block pl-1">Chrome User Data Directory</label>
                            <div className="relative">
                                <input
                                    type="text"
                                    className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 ring-indigo-500/10 focus:border-indigo-600 outline-none transition-all font-mono text-xs text-slate-700 pr-12"
                                    value={config.chromeUserDataDir}
                                    onChange={(e) => setConfig({ ...config, chromeUserDataDir: e.target.value })}
                                    placeholder="C:\Users\...\AppData\Local\Google\Chrome\User Data"
                                />
                                <FolderOpen className="absolute right-4 top-3.5 w-5 h-5 text-slate-400" />
                            </div>
                            <p className="text-[9px] text-slate-400 pl-1">Leave empty for Playwright's managed browser profile</p>
                        </div>
                    </div>
                </div>

                {/* Intelligence Modules */}
                <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm space-y-6">
                    <div className="flex items-center gap-2 text-indigo-600 mb-2">
                        <Bot className="w-5 h-5" />
                        <h3 className="font-black text-sm uppercase tracking-widest">Intelligence Modules</h3>
                    </div>

                    <div className="space-y-4">
                        <Toggle
                            label="NotebookLM Available"
                            description="Enable Google NotebookLM integration"
                            active={config.notebooklmAvailable}
                            onChange={() => setConfig({ ...config, notebooklmAvailable: !config.notebooklmAvailable })}
                        />

                        <Toggle
                            label="DeepSeek Available"
                            description="Enable DeepSeek AI integration"
                            active={config.deepseekAvailable}
                            onChange={() => setConfig({ ...config, deepseekAvailable: !config.deepseekAvailable })}
                        />

                        <div className="border-t border-slate-100 pt-4">
                            <div className="flex items-center justify-between p-4 bg-amber-50 rounded-2xl border border-amber-200">
                                <div>
                                    <div className="text-xs font-black text-amber-700 tracking-tight">NotebookLM Guided Mode</div>
                                    <div className="text-[10px] text-amber-600 font-medium mt-0.5">
                                        Copy prompts to clipboard, manually paste in NotebookLM
                                    </div>
                                </div>
                                <button
                                    onClick={() => setConfig({ ...config, notebooklmGuided: !config.notebooklmGuided })}
                                    className={`w-12 h-6 rounded-full relative transition-all ${config.notebooklmGuided ? 'bg-amber-500' : 'bg-slate-300'}`}
                                >
                                    <div className={`absolute w-4 h-4 rounded-full top-1 transition-all bg-white ${config.notebooklmGuided ? 'left-7 shadow-sm' : 'left-1'}`} />
                                </button>
                            </div>
                            <p className="text-[9px] text-slate-400 pl-1 mt-2">
                                Use when automated DOM interactions fail. Provides input keywords & output prompts for manual use.
                            </p>
                        </div>
                    </div>
                </div>

            </div>

             {/* Domain Management */}
            <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm space-y-6">
                <div className="flex items-center gap-2 text-indigo-600 mb-2">
                    <Globe className="w-5 h-5" />
                    <h3 className="font-black text-sm uppercase tracking-widest">Domain Management</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block pl-1">Trusted Domains</label>
                        <textarea
                            className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 ring-indigo-500/10 focus:border-indigo-600 outline-none transition-all font-mono text-xs text-slate-700 min-h-[100px]"
                            value={config.trustedDomains}
                            onChange={(e) => setConfig({ ...config, trustedDomains: e.target.value })}
                            placeholder="byjus.com, vedantu.com, khanacademy.org"
                        />
                        <p className="text-[9px] text-slate-400 pl-1">Comma-separated list of domains for 'Trusted' search mode.</p>
                    </div>

                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block pl-1">Blocked Domains</label>
                        <textarea
                            className="w-full px-5 py-3.5 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 ring-indigo-500/10 focus:border-indigo-600 outline-none transition-all font-mono text-xs text-slate-700 min-h-[100px]"
                            value={config.blockedDomains}
                            onChange={(e) => setConfig({ ...config, blockedDomains: e.target.value })}
                            placeholder="duckduckgo.com, youtube.com, ..."
                        />
                         <p className="text-[9px] text-slate-400 pl-1">Comma-separated list of domains to exclude from results.</p>
                    </div>
                </div>
            </div>

            {/* Environment Variables Section (Phase 4) */}
            <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-8 rounded-[2.5rem] border-2 border-purple-200 shadow-lg">
                <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-purple-600 rounded-xl text-white">
                        <Code className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-lg font-black text-slate-900 tracking-tight">Environment Variables</h3>
                        <p className="text-[10px] text-purple-600 font-bold uppercase tracking-widest">API Keys & Credentials</p>
                    </div>
                </div>

                <div className="space-y-5">
                    {/* Gemini API Key */}
                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block pl-1">
                            Gemini API Key
                        </label>
                        <div className="relative">
                            <input
                                type={config.showGeminiKey ? "text" : "password"}
                                placeholder="AIza..."
                                value={config.geminiApiKey || ''}
                                onChange={(e) => setConfig({ ...config, geminiApiKey: e.target.value })}
                                className="w-full px-5 py-3.5 pr-12 bg-white border border-purple-200 rounded-2xl focus:ring-4 ring-purple-500/10 focus:border-purple-600 outline-none transition-all font-mono text-sm text-slate-700"
                            />
                            <button
                                onClick={() => setConfig({ ...config, showGeminiKey: !config.showGeminiKey })}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {config.showGeminiKey ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    {/* OpenAI API Key */}
                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block pl-1">
                            OpenAI API Key
                        </label>
                        <div className="relative">
                            <input
                                type={config.showOpenAIKey ? "text" : "password"}
                                placeholder="sk-..."
                                value={config.openaiApiKey || ''}
                                onChange={(e) => setConfig({ ...config, openaiApiKey: e.target.value })}
                                className="w-full px-5 py-3.5 pr-12 bg-white border border-purple-200 rounded-2xl focus:ring-4 ring-purple-500/10 focus:border-purple-600 outline-none transition-all font-mono text-sm text-slate-700"
                            />
                            <button
                                onClick={() => setConfig({ ...config, showOpenAIKey: !config.showOpenAIKey })}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {config.showOpenAIKey ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    {/* DeepSeek API Key */}
                    <div className="space-y-2">
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block pl-1">
                            DeepSeek API Key
                        </label>
                        <div className="relative">
                            <input
                                type={config.showDeepSeekKey ? "text" : "password"}
                                placeholder="sk-..."
                                value={config.deepseekApiKey || ''}
                                onChange={(e) => setConfig({ ...config, deepseekApiKey: e.target.value })}
                                className="w-full px-5 py-3.5 pr-12 bg-white border border-purple-200 rounded-2xl focus:ring-4 ring-purple-500/10 focus:border-purple-600 outline-none transition-all font-mono text-sm text-slate-700"
                            />
                            <button
                                onClick={() => setConfig({ ...config, showDeepSeekKey: !config.showDeepSeekKey })}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            >
                                {config.showDeepSeekKey ? '🙈' : '👁️'}
                            </button>
                        </div>
                    </div>

                    <div className="p-4 bg-purple-100 border border-purple-200 rounded-2xl flex gap-3">
                        <AlertCircle className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
                        <div className="text-[10px] text-purple-800 font-medium leading-relaxed space-y-1">
                            <p className="font-bold">🔒 Security Note:</p>
                            <p>API keys are stored in browser localStorage. For production use, implement secure backend storage with encryption.</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-lg flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-emerald-50 rounded-2xl text-emerald-600">
                        <Server className="w-6 h-6" />
                    </div>
                    <div>
                        <div className="text-sm font-black text-slate-900 tracking-tight underline decoration-emerald-500 decoration-2 underline-offset-4">Commit Changes to Storage</div>
                        <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Configuration persists in localStorage</div>
                    </div>
                </div>
                <button
                    onClick={handleSave}
                    className="flex items-center gap-2 px-8 py-3.5 bg-emerald-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-emerald-100 hover:bg-emerald-700 transition-all active:scale-90"
                >
                    <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Configuration'}
                </button>
            </div>
        </div>
    );
};

export default ConfigTab;
