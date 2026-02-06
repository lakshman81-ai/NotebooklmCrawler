import React, { useState } from 'react';
import { MessageSquare, Link, FileText, Upload, Trash2, Send, Zap, Copy, Check, Info, AlertCircle, RefreshCw } from 'lucide-react';
import * as XLSX from 'xlsx';

const API_BASE = 'http://localhost:8000';

const InstructionToJulesTab = () => {
    const [repoUrl, setRepoUrl] = useState('');
    const [pastedData, setPastedData] = useState('');
    const [uploadedFile, setUploadedFile] = useState(null);
    const [mode, setMode] = useState('APPEND'); // APPEND or REPLACE
    const [generatedPrompt, setGeneratedPrompt] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [copied, setCopied] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [targetHeaders, setTargetHeaders] = useState([]);

    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (evt) => {
            const data = new Uint8Array(evt.target.result);
            const wb = XLSX.read(data, { type: 'array' });
            const wsname = wb.SheetNames[0];
            const ws = wb.Sheets[wsname];
            const jsonData = XLSX.utils.sheet_to_json(ws, { header: 1 });

            setUploadedFile({
                name: file.name,
                data: jsonData,
                size: file.size
            });
        };
        reader.readAsArrayBuffer(file);
    };

    const fetchHeaders = async (url) => {
        if (!url) return [];
        try {
            const response = await fetch(`${API_BASE}/api/proxy/headers?url=${encodeURIComponent(url)}`);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.headers || [];
        } catch (error) {
            console.error("Fetch error:", error);
            throw new Error("Failed to fetch target structure via proxy. Please check the URL.");
        }
    };

    const handleGeneratePrompt = async () => {
        setIsGenerating(true);
        setErrorMessage('');
        try {
            let headers = [];
            if (repoUrl) {
                headers = await fetchHeaders(repoUrl);
                setTargetHeaders(headers);
            }

            const inputData = uploadedFile ? JSON.stringify(uploadedFile.data) : pastedData;

            if (!inputData && !uploadedFile) {
                throw new Error("Please provide some input data (paste or upload).");
            }

            const prompt = generateOptimizedPrompt(headers, inputData, mode, repoUrl);
            setGeneratedPrompt(prompt);
        } catch (error) {
            setErrorMessage(error.message);
        } finally {
            setIsGenerating(false);
        }
    };

    const generateOptimizedPrompt = (headers, data, mode, url) => {
        const headerStr = headers.length > 0 ? headers.join(', ') : 'Extract from target repository';

        return `### INSTRUCTION FOR JULES (AI ASSISTANT) ###

I need you to process the following data and transform it into a specific structure.

**1. TARGET STRUCTURE:**
- **Repository Reference:** ${url || 'Not provided'}
- **Expected Headers:** [${headerStr}]
- **Mode:** ${mode === 'APPEND' ? 'Append to existing data' : 'Replace existing data / Full update'}

**2. INPUT DATA:**
\`\`\`
${data}
\`\`\`

**3. YOUR TASK:**
1. **Analyze the Input Data:** Understand the content, whether it's from Word, Excel, or a web copy-paste.
2. **Transform to Target Format:**
   - Map the input fields to the target headers: [${headerStr}].
   - If headers were not auto-fetched, please visit the repository link (if provided) or infer the best structure.
   - Ensure data types are consistent (e.g., numbers, dates, categories).
3. **Data Quality & Enrichment:**
   - Clean any artifacts from copy-pasting.
   - Standardize values.
   - **Brainstorming & Improvement:** Don't just copy. Brainstorm how this data can be made more effective. Suggest 3-5 specific improvements or additions to this dataset that would make it more valuable for its intended use case.
4. **Output Generation:**
   - Provide the final result in a clean CSV code block.
   - Followed by your "Brainstorming & Enhancement" section.

**4. CONTEXTUAL OPTIMIZATION:**
- If this is for a game or educational worksheet, ensure questions/answers are engaging and age-appropriate.
- Double-check for accuracy against the source material.

Please confirm you understand these instructions and provide the transformed data.`;
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(generatedPrompt);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center gap-4">
                <div className="p-3 bg-indigo-600 rounded-2xl text-white shadow-lg shadow-indigo-100">
                    <MessageSquare className="w-7 h-7" />
                </div>
                <div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Instruction to Jules</h2>
                    <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mt-1">
                        Generate optimized transformation prompts for Jules
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column: Inputs */}
                <div className="space-y-6">
                    {/* Repository URL */}
                    <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-50 rounded-xl text-blue-600">
                                <Link className="w-5 h-5" />
                            </div>
                            <h3 className="text-base font-black text-slate-800">Target Structure</h3>
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">
                                Repository CSV Raw Link
                            </label>
                            <input
                                type="text"
                                value={repoUrl}
                                onChange={(e) => setRepoUrl(e.target.value)}
                                placeholder="https://raw.githubusercontent.com/.../data.csv"
                                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm"
                            />
                            <div className="mt-2 flex flex-wrap gap-2">
                                <span className="text-[9px] text-slate-400 font-bold uppercase">Examples:</span>
                                {['Kani-Game-App', 'HarshiApp', 'Kani-Worksheet-App'].map(app => (
                                    <button
                                        key={app}
                                        onClick={() => setRepoUrl(`https://raw.githubusercontent.com/user/${app}/main/public/SKILL_GAMES_DATA.csv`)}
                                        className="text-[9px] bg-slate-100 hover:bg-slate-200 text-slate-600 px-2 py-0.5 rounded transition-all"
                                    >
                                        {app}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Data Input */}
                    <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-amber-50 rounded-xl text-amber-600">
                                    <FileText className="w-5 h-5" />
                                </div>
                                <h3 className="text-base font-black text-slate-800">Input Data</h3>
                            </div>
                            <div className="flex items-center gap-2">
                                <label className="cursor-pointer p-2 hover:bg-slate-50 rounded-lg transition-all text-slate-500 hover:text-indigo-600" title="Upload File">
                                    <Upload className="w-5 h-5" />
                                    <input type="file" className="hidden" accept=".csv,.xlsx,.xls" onChange={handleFileUpload} />
                                </label>
                                {uploadedFile && (
                                    <button onClick={() => setUploadedFile(null)} className="p-2 hover:bg-red-50 rounded-lg text-red-500 transition-all">
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                )}
                            </div>
                        </div>

                        {uploadedFile ? (
                            <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl flex items-center gap-3">
                                <Check className="text-emerald-500 w-5 h-5" />
                                <div>
                                    <p className="text-sm font-bold text-emerald-900">{uploadedFile.name}</p>
                                    <p className="text-[10px] text-emerald-600 font-bold uppercase">{Math.round(uploadedFile.size / 1024)} KB • Ready to transform</p>
                                </div>
                            </div>
                        ) : (
                            <textarea
                                value={pastedData}
                                onChange={(e) => setPastedData(e.target.value)}
                                placeholder="Paste Word, Excel, or CSV data here..."
                                className="w-full h-48 p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm resize-none font-mono"
                            />
                        )}
                    </div>

                    {/* Mode Selection */}
                    <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4 block">
                            Transformation Mode
                        </label>
                        <div className="flex gap-4">
                            <button
                                onClick={() => setMode('APPEND')}
                                className={`flex-1 py-3 px-4 rounded-xl text-sm font-bold border-2 transition-all ${mode === 'APPEND'
                                    ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                                    : 'border-slate-100 bg-slate-50 text-slate-500 hover:border-slate-200'
                                    }`}
                            >
                                Append Data
                            </button>
                            <button
                                onClick={() => setMode('REPLACE')}
                                className={`flex-1 py-3 px-4 rounded-xl text-sm font-bold border-2 transition-all ${mode === 'REPLACE'
                                    ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                                    : 'border-slate-100 bg-slate-50 text-slate-500 hover:border-slate-200'
                                    }`}
                            >
                                Replace Full
                            </button>
                        </div>
                    </div>

                    {/* Generate Button */}
                    <button
                        onClick={handleGeneratePrompt}
                        disabled={isGenerating || (!pastedData && !uploadedFile)}
                        className={`w-full py-4 rounded-2xl font-black text-sm uppercase tracking-[0.2em] transition-all flex items-center justify-center gap-3 shadow-xl ${isGenerating || (!pastedData && !uploadedFile)
                            ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            : 'bg-indigo-600 text-white hover:bg-indigo-500 shadow-indigo-100 active:scale-[0.98]'
                            }`}
                    >
                        {isGenerating ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
                        Generate Prompt for Jules
                    </button>

                    {errorMessage && (
                        <div className="p-4 bg-red-50 border border-red-100 rounded-xl flex items-start gap-3 animate-in slide-in-from-top-2">
                            <AlertCircle className="text-red-500 w-5 h-5 mt-0.5" />
                            <p className="text-xs font-bold text-red-800">{errorMessage}</p>
                        </div>
                    )}
                </div>

                {/* Right Column: Output */}
                <div className="space-y-6">
                    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-[2.5rem] p-8 shadow-2xl h-full flex flex-col">
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-indigo-500/20 rounded-xl flex items-center justify-center">
                                    <Send className="w-5 h-5 text-indigo-400" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-white">Generated Prompt</h3>
                                    <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Copy this to a new Jules session</p>
                                </div>
                            </div>
                            <button
                                onClick={copyToClipboard}
                                disabled={!generatedPrompt}
                                className={`p-3 rounded-xl transition-all ${copied
                                    ? 'bg-emerald-500 text-white'
                                    : 'bg-white/10 text-white hover:bg-white/20'
                                    }`}
                            >
                                {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                            </button>
                        </div>

                        <div className="flex-1 relative group">
                            <textarea
                                readOnly
                                value={generatedPrompt}
                                placeholder="Prompt will appear here after generation..."
                                className="w-full h-[500px] lg:h-full bg-slate-950/50 border border-white/10 rounded-2xl p-6 text-indigo-100 font-mono text-xs resize-none focus:outline-none scrollbar-thin scrollbar-thumb-white/10"
                            />
                            {!generatedPrompt && (
                                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 pointer-events-none">
                                    <Info className="w-8 h-8 mb-3 opacity-20" />
                                    <p className="text-sm font-bold opacity-40">Ready for transformation</p>
                                </div>
                            )}
                        </div>

                        {generatedPrompt && (
                            <div className="mt-6 p-4 bg-white/5 border border-white/10 rounded-xl">
                                <p className="text-[10px] text-indigo-300 font-bold uppercase tracking-widest mb-2">Pro Tip:</p>
                                <p className="text-[11px] text-slate-400 leading-relaxed italic">
                                    "This prompt is optimized to help Jules understand your source data structure and automatically transform it while providing creative brainstorming for your game or worksheet."
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InstructionToJulesTab;
