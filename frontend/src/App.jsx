import React, { useState } from 'react';
import Dashboard from './components/Dashboard/Dashboard';
import ConfigTab from './components/Config/ConfigTab';
import AdminTab from './components/Admin/AdminTab';
import TemplatesTab from './components/Templates/TemplatesTab';
import InstructionToJulesTab from './components/InstructionToJules/InstructionToJulesTab';
import { LayoutDashboard, Settings, ShieldAlert, Activity, FileSpreadsheet, MessageSquare } from 'lucide-react';

function App() {
    const [activeTab, setActiveTab] = useState('DASHBOARD');
    const [results, setResults] = useState(null);

    const renderContent = () => {
        switch (activeTab) {
            case 'DASHBOARD': return <Dashboard onCompileComplete={setResults} />;
            case 'CONFIG': return <ConfigTab />;
            case 'ADMIN': return <AdminTab />;
            case 'TEMPLATES': return <TemplatesTab />;
            case 'JULES': return <InstructionToJulesTab />;
            default: return <Dashboard />;
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
            <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-100">
                            <span className="text-white font-black text-2xl tracking-tighter">OC</span>
                        </div>
                        <div className="flex flex-col">
                            <h1 className="text-xl font-bold text-slate-900 tracking-tight leading-none">Orchestration Cockpit</h1>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-0.5">Automated Intelligence</span>
                        </div>
                    </div>

                    <nav className="hidden md:flex items-center gap-2">
                        <TabLink id="DASHBOARD" icon={<LayoutDashboard className="w-4 h-4" />} label="Dashboard" active={activeTab === 'DASHBOARD'} onClick={setActiveTab} />
                        <TabLink id="TEMPLATES" icon={<FileSpreadsheet className="w-4 h-4" />} label="Templates/Notebooklm O/P Prompt Generator" active={activeTab === 'TEMPLATES'} onClick={setActiveTab} />
                        <TabLink id="JULES" icon={<MessageSquare className="w-4 h-4" />} label="Instruction to Jules" active={activeTab === 'JULES'} onClick={setActiveTab} />
                        <TabLink id="CONFIG" icon={<Settings className="w-4 h-4" />} label="Config" active={activeTab === 'CONFIG'} onClick={setActiveTab} />
                        <TabLink id="ADMIN" icon={<ShieldAlert className="w-4 h-4" />} label="Admin" active={activeTab === 'ADMIN'} onClick={setActiveTab} />
                    </nav>

                    <div className="flex items-center gap-4">
                        <div className="hidden sm:flex px-3 py-1 bg-slate-100 rounded-full border border-slate-200 text-[10px] font-bold text-slate-500 uppercase tracking-tighter">
                            v2.2 Production
                        </div>
                        <div className="text-sm font-medium text-slate-600 border-l border-slate-200 pl-4 flex items-center gap-2">
                            <Activity className="w-3 h-3 text-emerald-500 animate-pulse" />
                            Live
                        </div>
                    </div>
                </div>
            </header>

            <main className="flex-1 max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
                {renderContent()}
            </main>

            <footer className="bg-white border-t border-slate-200 py-4 mt-auto">
                <div className="max-w-7xl mx-auto px-4 text-center text-[10px] text-slate-400 font-medium uppercase tracking-widest">
                    Secure Pipeline Environment • Strict Mode Enabled • Antigravity Engine
                </div>
            </footer>
        </div>
    );
}

const TabLink = ({ id, icon, label, active, onClick }) => (
    <button
        onClick={() => onClick(id)}
        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${active
            ? 'bg-indigo-50 text-indigo-700 shadow-sm'
            : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
            }`}
    >
        {icon}
        {label}
    </button>
);

export default App;
