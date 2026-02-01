import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * Individual prompt display box with copy and selection functionality
 */
const PromptOutputBox = ({ id, filename, prompt, selected, onSelect, onCopy }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(prompt);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        if (onCopy) onCopy(prompt);
    };

    return (
        <div className={`bg-white rounded-2xl border ${selected ? 'border-indigo-500 ring-2 ring-indigo-100' : 'border-slate-200'} p-5 shadow-sm relative transition-all hover:shadow-md`}>
            {/* Top Left: Checkbox */}
            <input
                type="checkbox"
                checked={selected}
                onChange={(e) => onSelect(id, e.target.checked)}
                className="absolute top-5 left-5 w-4 h-4 rounded accent-indigo-600 cursor-pointer"
            />

            {/* Top Right: Copy Button */}
            <button
                onClick={handleCopy}
                className={`absolute top-5 right-5 p-2 rounded-lg transition-all ${copied
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'text-slate-400 hover:text-indigo-600 hover:bg-indigo-50'
                    }`}
                title={copied ? "Copied!" : "Copy to clipboard"}
            >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>

            {/* Header: Filename */}
            <h4 className="font-bold text-sm text-slate-700 mt-6 mb-3 pr-10">
                {filename}
            </h4>

            {/* Body: Prompt Text (scrollable) */}
            <div className="text-xs text-slate-600 h-48 overflow-y-auto bg-slate-50 p-4 rounded-xl border border-slate-100 custom-scrollbar">
                <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed">
                    {prompt}
                </pre>
            </div>
        </div>
    );
};

export default PromptOutputBox;
