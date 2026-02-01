import React from 'react';
import { FileSpreadsheet, CheckSquare } from 'lucide-react';

/**
 * Predefined handout options
 */
const HANDOUT_OPTIONS = [
    { id: 'timeline', label: 'Timeline', description: 'Chronological view' },
    { id: 'flowchart', label: 'Flowchart', description: 'Process flow diagram' },
    { id: 'decision-tree', label: 'Decision Tree', description: 'Decision branching' },
    { id: 'mind-map', label: 'Mind Map', description: 'Visual connections' },
    { id: 'table', label: 'Table', description: 'Structured data' },
    { id: 'equation-helper', label: 'Equation Helper', description: 'Math formulas' },
    { id: 'tips', label: 'Tips', description: 'Quick tips and tricks' },
    { id: 'comparison', label: 'Comparison', description: 'Pro/con analysis' },
    { id: 'checklist', label: 'Checklist', description: 'Action items' }
];

const HandoutOptions = ({ selectedOptions, onOptionChange, manualEntry, onManualEntryChange }) => {
    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-5">
            {/* Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                <div className="p-2 bg-purple-50 rounded-xl">
                    <FileSpreadsheet className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                    <h3 className="text-base font-black text-slate-800">Handout Options</h3>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Select visualization types</p>
                </div>
            </div>

            {/* Checkbox Options Grid */}
            <div className="grid grid-cols-2 gap-3">
                {HANDOUT_OPTIONS.map(option => (
                    <label
                        key={option.id}
                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedOptions[option.id]
                            ? 'border-purple-500 bg-purple-50'
                            : 'border-slate-200 hover:border-purple-200 hover:bg-slate-50'
                            }`}
                    >
                        <input
                            type="checkbox"
                            checked={selectedOptions[option.id] || false}
                            onChange={(e) => onOptionChange(option.id, e.target.checked)}
                            className="mt-0.5 w-4 h-4 rounded accent-purple-600"
                        />
                        <div className="flex-1">
                            <div className="text-sm font-bold text-slate-700">{option.label}</div>
                            <div className="text-[10px] text-slate-500">{option.description}</div>
                        </div>
                    </label>
                ))}
            </div>

            {/* Manual Entry */}
            <div className="space-y-2 pt-3 border-t border-slate-100">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest pl-1">
                    Custom Handout Details
                </label>
                <textarea
                    value={manualEntry}
                    onChange={(e) => onManualEntryChange(e.target.value)}
                    placeholder="Add custom handout details (e.g., 'Add color coding', 'Include legend')..."
                    className="w-full h-20 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 placeholder:text-slate-400 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-100 resize-none"
                />
            </div>
        </div>
    );
};

export default HandoutOptions;
