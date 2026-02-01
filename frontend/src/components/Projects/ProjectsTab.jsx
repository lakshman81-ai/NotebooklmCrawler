import React, { useState, useEffect } from 'react';
import { FolderKanban, Search, Filter, FileText, Globe, Layers, Download, ExternalLink, Calendar, Trash2 } from 'lucide-react';

const ProjectsTab = () => {
    const [filter, setFilter] = useState('ALL');
    const [artifacts, setArtifacts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchArtifacts = async () => {
            try {
                const res = await fetch('http://localhost:3000/api/projects/list');
                const data = await res.json();
                if (data.artifacts) {
                    // Format dates and ensure consistent types
                    const formatted = data.artifacts.map(a => ({
                        ...a,
                        date: new Date(a.date * 1000).toISOString().split('T')[0],
                        score: a.score || 0.95 // Default score for now
                    }));
                    setArtifacts(formatted);
                }
                setLoading(false);
            } catch (e) {
                console.error("Artifact sync failed", e);
                setLoading(false);
            }
        };
        fetchArtifacts();
    }, []);

    const filtered = filter === 'ALL' ? artifacts : artifacts.filter(a => a.type === filter);

    return (
        <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-emerald-600 rounded-2xl text-white shadow-lg shadow-emerald-100">
                        <FolderKanban className="w-6 h-6" />
                    </div>
                    <div>
                        <h2 className="text-2xl font-black text-slate-900 tracking-tight">Project Artifacts</h2>
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Library / Discovery Cache / Logs</p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <div className="relative group">
                        <Search className="absolute left-4 top-3 w-4 h-4 text-slate-400" />
                        <input
                            placeholder="Find artifact..."
                            className="pl-12 pr-4 py-2.5 bg-white border border-slate-200 rounded-2xl text-xs font-bold outline-none focus:ring-4 ring-emerald-500/5 focus:border-emerald-600 transition-all shadow-sm w-64"
                        />
                    </div>
                    <button className="p-2.5 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-emerald-600 hover:border-emerald-600 transition-all">
                        <Filter className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">

                {/* Stats / Sidebar */}
                <div className="xl:col-span-1 space-y-6">
                    <div className="bg-slate-900 p-8 rounded-[2.5rem] border border-slate-800 shadow-2xl text-white relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10"><Layers className="w-24 h-24" /></div>
                        <div className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">TOTAL STORAGE</div>
                        <div className="text-3xl font-black tracking-tighter mb-4">42.4 GB</div>
                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-500 w-[65%]"></div>
                        </div>
                        <div className="mt-4 flex justify-between text-[10px] font-bold text-slate-500 italic">
                            <span>65% Allocated</span>
                            <span>Enterprise Tier</span>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-[2.5rem] border border-slate-200 shadow-sm space-y-2">
                        <FilterLink label="ALL PROTOCOLS" active={filter === 'ALL'} onClick={() => setFilter('ALL')} count={artifacts.length} />
                        <FilterLink label="FINAL SYNTHESIS" active={filter === 'FINAL'} onClick={() => setFilter('FINAL')} count={artifacts.filter(a => a.type === 'FINAL').length} color="indigo" />
                        <FilterLink label="CLEANED DOMS" active={filter === 'CLEANED'} onClick={() => setFilter('CLEANED')} count={artifacts.filter(a => a.type === 'CLEANED').length} color="emerald" />
                        <FilterLink label="RAW METADATA" active={filter === 'RAW'} onClick={() => setFilter('RAW')} count={artifacts.filter(a => a.type === 'RAW').length} color="amber" />
                    </div>
                </div>

                {/* Artifact List */}
                <div className="xl:col-span-3 space-y-4">
                    {loading ? (
                        <div className="flex flex-col items-center justify-center py-20 grayscale opacity-30 select-none animate-pulse">
                            <Layers className="w-16 h-16 text-slate-400 mb-4" />
                            <p className="text-[10px] font-black uppercase tracking-[0.3em]">Querying File System...</p>
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                            <p className="text-sm font-bold tracking-tight mb-2">No artifacts discovered yet.</p>
                            <p className="text-[10px] uppercase tracking-widest font-medium opacity-60">Initialize a mission in the Dashboard to begin synthesis.</p>
                        </div>
                    ) : filtered.map(art => (
                        <div key={art.id} className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm hover:shadow-xl hover:border-indigo-100 transition-all group flex items-center justify-between">
                            <div className="flex items-center gap-5">
                                <div className={`p-4 rounded-2xl ${art.type === 'FINAL' ? 'bg-indigo-50 text-indigo-600' : art.type === 'CLEANED' ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'} transition-colors`}>
                                    {art.type === 'FINAL' ? <FileText className="w-6 h-6" /> : art.type === 'CLEANED' ? <Globe className="w-6 h-6" /> : <Layers className="w-6 h-6" />}
                                </div>
                                <div>
                                    <h4 className="font-black text-slate-900 tracking-tight group-hover:text-indigo-600 transition-colors uppercase text-sm mb-1">{art.name}</h4>
                                    <div className="flex items-center gap-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                                        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {art.date}</span>
                                        <span className="flex items-center gap-1"><Layers className="w-3 h-3" /> {art.size}</span>
                                        <span className={`px-2 py-0.5 rounded-full ${art.score > 0.9 ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'} border border-current opacity-70`}>Quality: {art.score}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                <button className="p-3 bg-slate-50 border border-slate-100 rounded-2xl text-slate-400 hover:bg-white hover:border-indigo-600 hover:text-indigo-600 hover:shadow-lg transition-all active:scale-90">
                                    <Download className="w-5 h-5" />
                                </button>
                                <button className="p-3 bg-slate-50 border border-slate-100 rounded-2xl text-slate-400 hover:bg-white hover:border-indigo-600 hover:text-indigo-600 hover:shadow-lg transition-all active:scale-90">
                                    <ExternalLink className="w-5 h-5" />
                                </button>
                                <button className="p-3 bg-slate-50 border border-slate-100 rounded-2xl text-slate-400 hover:bg-white hover:border-red-600 hover:text-red-600 hover:shadow-lg transition-all active:scale-90">
                                    <Trash2 className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

            </div>
        </div>
    );
};

const FilterLink = ({ label, active, onClick, count, color = 'slate' }) => {
    const activeColors = {
        indigo: 'bg-indigo-50 text-indigo-700 font-black',
        emerald: 'bg-emerald-50 text-emerald-700 font-black',
        amber: 'bg-amber-50 text-amber-700 font-black',
        slate: 'bg-slate-100 text-slate-900 font-black'
    };

    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center justify-between px-6 py-4 rounded-2xl text-[10px] tracking-widest transition-all ${active ? activeColors[color] : 'text-slate-400 hover:bg-slate-50 font-bold'}`}
        >
            <span>{label}</span>
            <span className={`px-2 py-0.5 rounded-lg text-[9px] ${active ? 'bg-white shadow-sm' : 'bg-slate-100'}`}>{count}</span>
        </button>
    );
};

export default ProjectsTab;
