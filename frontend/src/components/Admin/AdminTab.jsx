import React, { useState } from 'react';
import { ShieldAlert, Key, Zap, Lock, Eye, EyeOff, Save, Check } from 'lucide-react';

// --- Sub-components (Defined first) ---

const ApiKeyInput = ({ label, value, onChange, visible, onToggle, icon, placeholder = "••••••••••••••••••••••••••••••••" }) => (
    <div className="space-y-2">
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest flex items-center gap-2 pl-1">
            {icon}
            {label}
        </label>
        <div className="relative group">
            <input
                type={visible ? 'text' : 'password'}
                className="w-full px-5 py-4 bg-slate-50 border border-slate-200 rounded-2xl focus:ring-4 ring-indigo-500/5 focus:border-indigo-600 outline-none transition-all font-mono text-sm shadow-inner placeholder-slate-300"
                placeholder={placeholder}
                value={value}
                onChange={(e) => onChange(e.target.value)}
            />
            <button
                onClick={onToggle}
                className="absolute right-4 top-4 text-slate-400 hover:text-indigo-600 transition-colors"
            >
                {visible ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
        </div>
    </div>
);

// --- Main Component ---

const AdminTab = () => {
    const [keys, setKeys] = useState({
        deepseek: '',
        gemini: '',
        notebooklm: 'DOM_SIM_ACTIVE',
        proxy: ''
    });

    const [showKeys, setShowKeys] = useState({});
    const [saved, setSaved] = useState(false);

    const toggleVisible = (id) => setShowKeys({ ...showKeys, [id]: !showKeys[id] });

    const handleSave = async () => {
        try {
            const res = await fetch('http://localhost:3000/api/admin/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(keys)
            });
            if (res.ok) {
                setSaved(true);
                setTimeout(() => setSaved(false), 2000);
            }
        } catch (e) {
            alert("Security Sync Failed");
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-4 mb-2">
                <div className="p-3 bg-red-600 rounded-2xl text-white shadow-lg shadow-red-100">
                    <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                    <h2 className="text-2xl font-black text-slate-900 tracking-tight">Security & Admin</h2>
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Secret Management • Identity Verification</p>
                </div>
            </div>

            <div className="bg-white p-10 rounded-[2.5rem] border border-slate-200 shadow-sm space-y-10">
                <div className="space-y-6">
                    <ApiKeyInput
                        label="DeepSeek API Secret"
                        value={keys.deepseek}
                        onChange={(val) => setKeys({ ...keys, deepseek: val })}
                        visible={showKeys['deepseek']}
                        onToggle={() => toggleVisible('deepseek')}
                        icon={<Zap className="w-4 h-4 text-amber-500" />}
                    />

                    <ApiKeyInput
                        label="Google Gemini Key"
                        value={keys.gemini}
                        onChange={(val) => setKeys({ ...keys, gemini: val })}
                        visible={showKeys['gemini']}
                        onToggle={() => toggleVisible('gemini')}
                        icon={<Lock className="w-4 h-4 text-indigo-500" />}
                    />

                    <div className="opacity-40 select-none grayscale cursor-not-allowed">
                        <ApiKeyInput
                            label="Residential Proxy Endpoint"
                            value={keys.proxy}
                            onChange={() => { }}
                            visible={false}
                            onToggle={() => { }}
                            icon={<Zap className="w-4 h-4 text-slate-400" />}
                            placeholder="Optional for high-volume crawling"
                        />
                    </div>
                </div>

                <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                    <div className="flex items-center gap-3 text-[10px] text-slate-400 font-bold uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                        Vault is Encrypted (AES-256)
                    </div>
                    <button
                        onClick={handleSave}
                        className={`flex items-center gap-2 px-10 py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] transition-all shadow-2xl ${saved ? 'bg-emerald-600 text-white shadow-emerald-100' : 'bg-red-600 text-white shadow-red-100 hover:bg-red-700 active:scale-95'
                            }`}
                    >
                        {saved ? <><Check className="w-4 h-4" /> SECRETS SYNCED</> : <><Save className="w-4 h-4" /> COMMIT SECRETS</>}
                    </button>
                </div>
            </div>

            {/* Admin Audit Log (Mock) */}
            <div className="bg-slate-950 p-8 rounded-[2.5rem] border border-white/5 shadow-2xl space-y-4">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Admin Access Log</h3>
                    <div className="px-3 py-1 bg-red-500/10 border border-red-500/20 rounded-full text-[8px] font-black text-red-500 uppercase tracking-tighter">RESTRICTED</div>
                </div>
                <div className="font-mono text-[9px] text-slate-500 space-y-1">
                    <p>[2026-01-29 23:35:12] - Identity challenge: ANTIGRAVITY_AGENT_OK</p>
                    <p>[2026-01-29 23:34:01] - Secret rotation initiated for Gemini Backend</p>
                    <p className="text-red-900/50">[2026-01-28 12:00:00] - UNAUTHORIZED ATTEMPT_BLOCKED_BY_WAF</p>
                </div>
            </div>
        </div>
    );
};

export default AdminTab;
