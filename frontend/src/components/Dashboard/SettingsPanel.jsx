import React, { useState } from 'react';
import { Shield, Globe, Video, UserCheck, Bot, Cpu, Zap, Search } from 'lucide-react';
import { checkBackendHealth } from '../../services/apiConfig';

const SettingsPanel = ({ settings, setSettings }) => {
    const [testStatus, setTestStatus] = useState(null); // null, 'testing', 'success', 'error'

    const toggleMode = (mode) => {
        setSettings(prev => ({
            ...prev,
            modes: { ...prev.modes, [mode]: !prev.modes[mode] }
        }));
    };

    const testConnection = async () => {
        setTestStatus('testing');
        const isHealthy = await checkBackendHealth();
        setTestStatus(isHealthy ? 'success' : 'error');
    };

    return (
        <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm space-y-8">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-600 rounded-xl text-white shadow-lg shadow-indigo-100">
                    <Shield className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-black text-slate-900 tracking-tight underline decoration-indigo-500 decoration-4 underline-offset-4">CONFIGURATION</h3>
            </div>

            <div className="space-y-8">
                {/* API Key Section */}
                <div className="space-y-3">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Zap className="w-3 h-3 text-amber-500" />
                        AI INFERENCE BACKEND (DEEPSEEK / OPENAI)
                    </label>
                    <div className="flex gap-3">
                        <input
                            type="password"
                            className="w-full px-5 py-3 border border-slate-200 rounded-2xl focus:ring-4 ring-indigo-500/10 focus:border-indigo-500 outline-none transition-all font-mono text-sm shadow-sm"
                            placeholder="sk-deepseek-••••••••••••"
                            value={settings.apiKey}
                            onChange={e => setSettings({ ...settings, apiKey: e.target.value })}
                        />
                        <button
                            onClick={testConnection}
                            className={`px-6 py-3 rounded-2xl text-xs font-black uppercase tracking-widest transition-all border-2 ${testStatus === 'success' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                                testStatus === 'error' ? 'bg-red-50 text-red-700 border-red-200' :
                                    'bg-white text-slate-600 border-slate-200 hover:border-indigo-500 hover:text-indigo-600'
                                } shadow-sm`}
                        >
                            {testStatus === 'testing' ? '...' :
                                testStatus === 'success' ? 'VALID' :
                                    testStatus === 'error' ? 'FAIL' : 'TEST'}
                        </button>
                    </div>
                </div>

                {/* Google Search API Section */}
                <div className="space-y-3 animate-in fade-in slide-in-from-top-2">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                        <Search className="w-3 h-3 text-blue-500" />
                        GOOGLE SEARCH API (OPTIONAL FALLBACK)
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                        <input
                            type="password"
                            className="w-full px-5 py-3 border border-slate-200 rounded-2xl focus:ring-4 ring-blue-500/10 focus:border-blue-500 outline-none transition-all font-mono text-sm shadow-sm"
                            placeholder="API Key (AIza...)"
                            value={settings.googleApiKey || ''}
                            onChange={e => setSettings({ ...settings, googleApiKey: e.target.value })}
                        />
                        <input
                            type="text"
                            className="w-full px-5 py-3 border border-slate-200 rounded-2xl focus:ring-4 ring-blue-500/10 focus:border-blue-500 outline-none transition-all font-mono text-sm shadow-sm"
                            placeholder="Search Engine ID (CX)"
                            value={settings.googleCx || ''}
                            onChange={e => setSettings({ ...settings, googleCx: e.target.value })}
                        />
                    </div>
                    <p className="text-[10px] text-slate-400 pl-2">Used only if DuckDuckGo fails. Leave empty to rely on DDG.</p>
                </div>

                {/* NotebookLM Injection Mode Toggle */}
                <div className="p-4 bg-amber-50 rounded-2xl border border-amber-100 flex items-center justify-between">
                    <div>
                        <div className="text-xs font-black text-amber-900 uppercase tracking-wider mb-1">NotebookLM DOM Injection</div>
                        <div className="text-[10px] text-amber-700 font-medium">Use legacy JavaScript injection instead of Clipboard Paste (Backup only).</div>
                    </div>
                    <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                        <input
                            type="checkbox"
                            name="toggle"
                            id="injection-toggle"
                            className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer transition-all duration-300 transform translate-x-0 checked:translate-x-6 checked:border-amber-500"
                            checked={settings.notebooklmInjectionMode || false}
                            onChange={(e) => setSettings({...settings, notebooklmInjectionMode: e.target.checked})}
                        />
                        <label htmlFor="injection-toggle" className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer transition-colors ${settings.notebooklmInjectionMode ? 'bg-amber-500' : 'bg-amber-200'}`}></label>
                    </div>
                </div>


                <div className="w-full h-px bg-slate-100"></div>

                {/* Source Modes */}
                <div className="space-y-4">
                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4">ACTIVE INTELLIGENCE MODULES</label>

                    <ModeToggle
                        label="MODE ALPHA"
                        desc="Trusted Source Handlers (Byjus, Vedantu)"
                        active={settings.modes.A}
                        onChange={() => toggleMode('A')}
                        icon={<UserCheck className="w-5 h-5" />}
                        color="indigo"
                    />

                    <ModeToggle
                        label="MODE BETA"
                        desc="Deep Web Crawling & Discovery"
                        active={settings.modes.B}
                        onChange={() => toggleMode('B')}
                        icon={<Globe className="w-5 h-5" />}
                        color="emerald"
                    />

                    <div className="opacity-20 pointer-events-none filter grayscale">
                        <ModeToggle
                            label="MODE GAMMA (N/A)"
                            desc="YouTube Multi-Stage Research"
                            active={settings.modes.C}
                            onChange={() => { }}
                            icon={<Video className="w-5 h-5" />}
                            color="slate"
                        />
                    </div>

                    <ModeToggle
                        label="AGENTIC MODE"
                        desc="NotebookLM DOM Orchestration"
                        active={settings.modes.D}
                        onChange={() => toggleMode('D')}
                        icon={<Bot className="w-5 h-5" />}
                        color="amber"
                    />
                </div>
            </div>

            <div className="pt-6 border-t border-slate-100 italic text-[10px] text-slate-400 font-medium">
                Hardware acceleration enabled for Mode B.
            </div>
        </div>
    );
};

const ModeToggle = ({ label, desc, active, onChange, icon, color }) => {
    const colorClasses = {
        indigo: active ? 'border-indigo-500/50 bg-indigo-50/50' : 'border-slate-100 bg-white',
        emerald: active ? 'border-emerald-500/50 bg-emerald-50/50' : 'border-slate-100 bg-white',
        amber: active ? 'border-amber-500/50 bg-amber-50/50' : 'border-slate-100 bg-white',
        slate: 'border-slate-100 bg-white'
    };

    const iconClasses = {
        indigo: active ? 'bg-indigo-600 text-white shadow-indigo-100' : 'bg-slate-50 text-slate-400',
        emerald: active ? 'bg-emerald-600 text-white shadow-emerald-100' : 'bg-slate-50 text-slate-400',
        amber: active ? 'bg-amber-600 text-white shadow-amber-100' : 'bg-slate-50 text-slate-400',
        slate: 'bg-slate-50 text-slate-400'
    };

    return (
        <div
            onClick={onChange}
            className={`p-5 rounded-2xl border-2 cursor-pointer transition-all flex items-center justify-between group h-24 ${colorClasses[color]} ${active ? 'shadow-lg shadow-slate-100 -translate-y-0.5' : 'hover:border-slate-200'}`}
        >
            <div className="flex items-center gap-4">
                <div className={`p-3 rounded-2xl transition-all shadow-md ${iconClasses[color]}`}>
                    {icon}
                </div>
                <div>
                    <div className={`font-black text-sm tracking-tight ${active ? 'text-slate-900' : 'text-slate-400'}`}>{label}</div>
                    <div className={`text-[10px] font-bold uppercase tracking-widest ${active ? 'text-slate-500' : 'text-slate-300'}`}>{desc}</div>
                </div>
            </div>
            <div className={`w-12 h-6 rounded-full relative transition-all duration-300 ${active ? 'bg-indigo-600 shadow-inner' : 'bg-slate-200'}`}>
                <div className={`absolute w-4 h-4 bg-white rounded-full top-1 transition-all duration-300 shadow-md ${active ? 'left-7' : 'left-1'}`} />
            </div>
        </div>
    );
};

export default SettingsPanel;
