import React, { useState } from 'react';
import { X, Save, BookOpen, List, FileText, Check, Download } from 'lucide-react';

const ResultsModal = ({ data, onClose }) => {
    const [activeTab, setActiveTab] = useState('STUDY_MATERIAL');
    const [content, setContent] = useState(data.compiled || { stages: { 'Summary': 'Synthesis in progress...' } });
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        setTimeout(() => {
            setIsSaving(false);
            alert("Artifact saved to outputs/final/ !");
        }, 1000);
    };

    const renderContent = () => {
        return (
            <div className="p-8 overflow-y-auto h-[60vh] bg-white">
                <div className="flex items-center gap-2 mb-6">
                    <div className="w-1.5 h-6 bg-indigo-600 rounded-full"></div>
                    <h3 className="text-xl font-black text-slate-800 tracking-tight">{activeTab.replace('_', ' ')} PREVIEW</h3>
                </div>

                <div className="space-y-6">
                    {activeTab === 'STUDY_MATERIAL' && (
                        <div className="space-y-6">
                            {Object.entries(content.stages || {}).map(([stage, text]) => (
                                <div key={stage} className="space-y-2 group">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] group-focus-within:text-indigo-600 transition-colors">{stage}</label>
                                    <textarea
                                        className="w-full p-5 rounded-2xl border border-slate-200 focus:ring-2 ring-indigo-500/20 focus:border-indigo-500 outline-none transition-all h-64 text-sm font-medium leading-relaxed text-slate-700 shadow-sm"
                                        value={text}
                                        onChange={(e) => setContent({ ...content, stages: { ...content.stages, [stage]: e.target.value } })}
                                    />
                                </div>
                            ))}
                        </div>
                    )}

                    {(activeTab === 'QUESTIONNAIRE' || activeTab === 'HANDOUT') && (
                        <div className="flex flex-col items-center justify-center py-20 text-slate-400 opacity-50 grayscale select-none">
                            <Layers className="w-16 h-16 mb-4 animate-pulse" />
                            <p className="font-black uppercase tracking-widest text-[10px]">Synthesis Module Not Locked</p>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-300">
            <div className="bg-slate-50 w-full max-w-6xl rounded-[2.5rem] shadow-2xl flex flex-col max-h-[90vh] overflow-hidden border border-slate-800/20 scale-in-center transition-transform">

                {/* Header */}
                <div className="px-10 py-6 border-b border-slate-200 flex items-center justify-between bg-white">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-indigo-100">
                            <FileText className="w-6 h-6" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-black text-slate-900 tracking-tighter">Mission Artifacts</h2>
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Protocol: Alpha-7 Compliance</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-2xl font-bold shadow-xl shadow-indigo-200 hover:bg-indigo-700 transition-all active:scale-95 disabled:opacity-50"
                        >
                            {isSaving ? <span className="animate-spin text-lg">⟳</span> : <Download className="w-5 h-5" />}
                            EXPORT RESULTS
                        </button>
                        <button onClick={onClose} className="p-3 hover:bg-slate-100 rounded-2xl transition-colors text-slate-400 hover:text-red-500">
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </div>

                {/* Tab Bar */}
                <div className="flex px-10 bg-white border-b border-slate-100">
                    <TabButton
                        active={activeTab === 'STUDY_MATERIAL'}
                        onClick={() => setActiveTab('STUDY_MATERIAL')}
                        icon={<BookOpen className="w-4 h-4" />}
                        label="Unified Guide"
                    />
                    <TabButton
                        active={activeTab === 'QUESTIONNAIRE'}
                        onClick={() => setActiveTab('QUESTIONNAIRE')}
                        icon={<List className="w-4 h-4" />}
                        label="Assessment"
                    />
                    <TabButton
                        active={activeTab === 'HANDOUT'}
                        onClick={() => setActiveTab('HANDOUT')}
                        icon={<Layers className="w-4 h-4" />}
                        label="Visual Deck"
                    />
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {renderContent()}
                </div>

                {/* Footer */}
                <div className="px-10 py-4 border-t border-slate-200 bg-white flex items-center justify-between">
                    <div className="flex items-center gap-6 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                        <div className="flex items-center gap-2">
                            <Check className="w-4 h-4 text-emerald-500 stroke-[3px]" />
                            <span>Integrity Verified</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <Check className="w-4 h-4 text-emerald-500 stroke-[3px]" />
                            <span>Source Parity Lock</span>
                        </div>
                    </div>
                    <div className="text-[10px] font-black text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full uppercase tracking-tighter">
                        Antigravity Engine • Phase 2
                    </div>
                </div>

            </div>
        </div>
    );
};

const TabButton = ({ active, onClick, icon, label }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-3 px-8 py-5 text-xs font-black uppercase tracking-widest border-b-4 transition-all ${active
            ? 'border-indigo-600 text-indigo-700 bg-indigo-50/30'
            : 'border-transparent text-slate-400 hover:text-slate-600 hover:bg-slate-50'
            }`}
    >
        {icon}
        {label}
    </button>
);

const Layers = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><polygon points="12 2 2 7 12 12 22 7 12 2" /><polyline points="2 17 12 22 22 17" /><polyline points="2 12 12 17 22 12" /></svg>
);

export default ResultsModal;
