import React, { useState, useEffect } from 'react';
import { Globe, RefreshCw, Plus } from 'lucide-react';
import { API_BASE_URL } from '../../services/apiConfig';

const ExternalSourcePanel = ({ onAddPrompt }) => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [preview, setPreview] = useState('');
    const [headers, setHeaders] = useState([]);

    const handleGenerate = async () => {
        if (!url) return;
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/proxy/headers?url=${encodeURIComponent(url)}`);
            const data = await response.json();
            if (data.success) {
                // Generate header-only string
                const headerString = data.headers ? data.headers.join(', ') : '';
                setPreview(headerString);
                setHeaders(data.headers);
            } else {
                 setPreview('Error: ' + (data.detail || 'Failed to fetch'));
            }
        } catch (e) {
            setPreview('Error: ' + e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = () => {
        onAddPrompt({
            id: `ext-${Date.now()}`,
            filename: url,
            source: 'External URL',
            structure: preview,
            headers: headers
        });
        setUrl('');
        setPreview('');
    };

    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-5 h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100 flex-shrink-0">
                 <div className="p-2 bg-pink-50 rounded-xl">
                    <Globe className="w-5 h-5 text-pink-600" />
                </div>
                <div>
                    <h3 className="text-base font-black text-slate-800">External Source</h3>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                        Load from GitHub URL
                    </p>
                </div>
            </div>

            <div className="space-y-3 flex-shrink-0">
                <label className="text-[10px] font-bold text-slate-400 uppercase">Input Source</label>
                <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://raw.githubusercontent.com/..."
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium focus:outline-none focus:border-pink-500 transition-colors"
                />

                <button
                    onClick={handleGenerate}
                    disabled={loading || !url}
                    className="w-full flex items-center justify-center gap-2 py-3 bg-pink-600 hover:bg-pink-700 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? <RefreshCw className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                    {loading ? 'Analyzing...' : 'Generate Headers'}
                </button>
            </div>

            {preview && (
                <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 flex-grow flex flex-col min-h-0">
                    <div className="space-y-1 flex-grow flex flex-col min-h-0">
                        <label className="text-[10px] font-bold text-slate-400 uppercase">Structure Preview (Editable)</label>
                        <textarea
                            value={preview}
                            onChange={(e) => setPreview(e.target.value)}
                            className="w-full flex-grow p-3 bg-slate-50 border border-slate-200 rounded-xl text-[10px] font-mono text-slate-600 focus:outline-none focus:border-pink-500 resize-none min-h-[150px]"
                        />
                    </div>
                    <button
                        onClick={handleAdd}
                        className="w-full flex-shrink-0 flex items-center justify-center gap-2 py-3 border-2 border-pink-100 hover:border-pink-200 text-pink-600 rounded-xl text-xs font-bold transition-all hover:bg-pink-50"
                    >
                        <Plus className="w-3 h-3" />
                        Add to Prompts
                    </button>
                </div>
            )}
        </div>
    );
};

export default ExternalSourcePanel;
