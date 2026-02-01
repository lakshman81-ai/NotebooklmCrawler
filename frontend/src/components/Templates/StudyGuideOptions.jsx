import React from 'react';
import { CheckSquare, Square } from 'lucide-react';

/**
 * Predefined study guide options
 */
const STUDY_GUIDE_OPTIONS = [
    { id: 'assertion', label: 'Assertion', description: 'Key statements and claims' },
    { id: 'concept', label: 'Concept', description: 'Core concepts and definitions' },
    { id: 'clarification', label: 'Clarification', description: 'Explanation of complex ideas' },
    { id: 'examples', label: 'Examples', description: 'Illustrative examples' },
    { id: 'summary', label: 'Summary', description: 'Concise overview' },
    { id: 'key-terms', label: 'Key Terms', description: 'Important vocabulary' },
    { id: 'csv-format', label: 'CSV/Excel Format', description: 'Output in required CSV headers' }
];

const StudyGuideOptions = ({ selectedOptions, onOptionChange, manualEntry, onManualEntryChange }) => {
    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-5">
            {/* Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                <div className="p-2 bg-blue-50 rounded-xl">
                    <CheckSquare className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                    <h3 className="text-base font-black text-slate-800">Study Guide Options</h3>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Select elements to include</p>
                </div>
            </div>

            {/* Checkbox Options Grid */}
            <div className="grid grid-cols-2 gap-3">
                {STUDY_GUIDE_OPTIONS.map(option => (
                    <label
                        key={option.id}
                        className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${selectedOptions[option.id]
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-slate-200 hover:border-indigo-200 hover:bg-slate-50'
                            }`}
                    >
                        <input
                            type="checkbox"
                            checked={selectedOptions[option.id] || false}
                            onChange={(e) => onOptionChange(option.id, e.target.checked)}
                            className="mt-0.5 w-4 h-4 rounded accent-indigo-600"
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
                    Custom Instructions
                </label>
                <textarea
                    value={manualEntry}
                    onChange={(e) => onManualEntryChange(e.target.value)}
                    placeholder="Add custom study guide instructions..."
                    className="w-full h-20 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 placeholder:text-slate-400 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 resize-none"
                />
            </div>
        </div>
    );
};

export default StudyGuideOptions;
