import React, { useState } from 'react';
import { FolderOpen, ChevronDown, ChevronRight, File } from 'lucide-react';

/**
 * Template file structure
 */
const TEMPLATE_SOURCES = {
    Kani: {
        GameApp: [
            { id: 'kani-gameapp-english', filename: 'ENGLISH_GOOGLE_SHEET_DATA.csv', path: 'Kani/GameApp/ENGLISH_GOOGLE_SHEET_DATA.csv' },
            { id: 'kani-gameapp-math', filename: 'MATH_GOOGLE_SHEET_DATA.csv', path: 'Kani/GameApp/MATH_GOOGLE_SHEET_DATA.csv' },
            { id: 'kani-gameapp-skill', filename: 'SKILL_GAMES_DATA.csv', path: 'Kani/GameApp/SKILL_GAMES_DATA.csv' }
        ],
        Worksheet: [
            { id: 'kani-worksheet', filename: 'worksheet_template.csv', path: 'Kani/Worksheet/worksheet_template.csv' }
        ]
    },
    Harshitha: [
        { id: 'harshitha-biology', filename: 'biology.xlsx', path: 'Harshitha/biology.xlsx' },
        { id: 'harshitha-chemistry', filename: 'chemistry.xlsx', path: 'Harshitha/chemistry.xlsx' },
        { id: 'harshitha-math', filename: 'math.xlsx', path: 'Harshitha/math.xlsx' },
        { id: 'harshitha-physics', filename: 'physics.xlsx', path: 'Harshitha/physics.xlsx' }
    ]
};

const TemplateSourcesPanel = ({ selectedSources, onSelectionChange }) => {
    const [expandedSections, setExpandedSections] = useState({
        Kani: true,
        'Kani-GameApp': true,
        'Kani-Worksheet': true,
        Harshitha: true
    });

    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    const handleSelectAll = (source, files) => {
        const allSelected = files.every(f => selectedSources.has(f.id));
        files.forEach(file => {
            onSelectionChange(file.id, !allSelected, file);
        });
    };

    const renderKaniSection = () => {
        const kaniFiles = [...TEMPLATE_SOURCES.Kani.GameApp, ...TEMPLATE_SOURCES.Kani.Worksheet];
        const allSelected = kaniFiles.every(f => selectedSources.has(f.id));
        const someSelected = kaniFiles.some(f => selectedSources.has(f.id));

        return (
            <div className="space-y-2">
                <div
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-all"
                    onClick={() => toggleSection('Kani')}
                >
                    <div className="flex items-center gap-2">
                        {expandedSections.Kani ? (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                        ) : (
                            <ChevronRight className="w-4 h-4 text-slate-400" />
                        )}
                        <FolderOpen className="w-4 h-4 text-amber-500" />
                        <span className="text-sm font-bold text-slate-700">Kani Templates</span>
                        <span className="text-xs text-slate-400 font-medium ml-1">
                            ({TEMPLATE_SOURCES.Kani.GameApp.length + TEMPLATE_SOURCES.Kani.Worksheet.length})
                        </span>
                    </div>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            handleSelectAll('Kani', kaniFiles);
                        }}
                        className="text-xs font-bold text-indigo-600 hover:text-indigo-700 px-2 py-1 rounded hover:bg-indigo-50"
                    >
                        {allSelected ? 'Deselect All' : 'Select All'}
                    </button>
                </div>

                {expandedSections.Kani && (
                    <div className="ml-4 space-y-1">
                        {/* GameApp Subsection */}
                        <div>
                            <div
                                className="flex items-center gap-2 p-2 pl-4 rounded-lg hover:bg-slate-50 cursor-pointer"
                                onClick={() => toggleSection('Kani-GameApp')}
                            >
                                {expandedSections['Kani-GameApp'] ? (
                                    <ChevronDown className="w-3 h-3 text-slate-400" />
                                ) : (
                                    <ChevronRight className="w-3 h-3 text-slate-400" />
                                )}
                                <span className="text-xs font-bold text-slate-600">GameApp</span>
                            </div>
                            {expandedSections['Kani-GameApp'] && (
                                <div className="ml-6 space-y-1">
                                    {TEMPLATE_SOURCES.Kani.GameApp.map(file => (
                                        <FileCheckbox
                                            key={file.id}
                                            file={file}
                                            selected={selectedSources.has(file.id)}
                                            onSelect={onSelectionChange}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Worksheet Subsection */}
                        <div>
                            <div
                                className="flex items-center gap-2 p-2 pl-4 rounded-lg hover:bg-slate-50 cursor-pointer"
                                onClick={() => toggleSection('Kani-Worksheet')}
                            >
                                {expandedSections['Kani-Worksheet'] ? (
                                    <ChevronDown className="w-3 h-3 text-slate-400" />
                                ) : (
                                    <ChevronRight className="w-3 h-3 text-slate-400" />
                                )}
                                <span className="text-xs font-bold text-slate-600">Worksheet</span>
                            </div>
                            {expandedSections['Kani-Worksheet'] && (
                                <div className="ml-6 space-y-1">
                                    {TEMPLATE_SOURCES.Kani.Worksheet.map(file => (
                                        <FileCheckbox
                                            key={file.id}
                                            file={file}
                                            selected={selectedSources.has(file.id)}
                                            onSelect={onSelectionChange}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderHarshithaSection = () => {
        const files = TEMPLATE_SOURCES.Harshitha;
        const allSelected = files.every(f => selectedSources.has(f.id));

        return (
            <div className="space-y-2">
                <div
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-all"
                    onClick={() => toggleSection('Harshitha')}
                >
                    <div className="flex items-center gap-2">
                        {expandedSections.Harshitha ? (
                            <ChevronDown className="w-4 h-4 text-slate-400" />
                        ) : (
                            <ChevronRight className="w-4 h-4 text-slate-400" />
                        )}
                        <FolderOpen className="w-4 h-4 text-blue-500" />
                        <span className="text-sm font-bold text-slate-700">Harshitha Templates</span>
                        <span className="text-xs text-slate-400 font-medium ml-1">
                            ({files.length})
                        </span>
                    </div>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            handleSelectAll('Harshitha', files);
                        }}
                        className="text-xs font-bold text-indigo-600 hover:text-indigo-700 px-2 py-1 rounded hover:bg-indigo-50"
                    >
                        {allSelected ? 'Deselect All' : 'Select All'}
                    </button>
                </div>

                {expandedSections.Harshitha && (
                    <div className="ml-4 space-y-1">
                        {files.map(file => (
                            <FileCheckbox
                                key={file.id}
                                file={file}
                                selected={selectedSources.has(file.id)}
                                onSelect={onSelectionChange}
                            />
                        ))}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-5">
            {/* Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                <div className="p-2 bg-indigo-50 rounded-xl">
                    <FolderOpen className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                    <h3 className="text-base font-black text-slate-800">Template Sources</h3>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                        Select files to generate prompts
                    </p>
                </div>
            </div>

            {/* File Tree */}
            <div className="space-y-4 max-h-96 overflow-y-auto custom-scrollbar pr-2">
                {renderKaniSection()}
                {renderHarshithaSection()}
            </div>

            {/* Footer Stats */}
            <div className="pt-4 border-t border-slate-100">
                <p className="text-xs font-bold text-slate-500">
                    {selectedSources.size} file{selectedSources.size !== 1 ? 's' : ''} selected
                </p>
            </div>
        </div>
    );
};

/**
 * Individual file checkbox component
 */
const FileCheckbox = ({ file, selected, onSelect }) => {
    return (
        <label className={`flex items-center gap-2 p-2 pl-4 rounded-lg cursor-pointer transition-all ${selected
            ? 'bg-indigo-50 border border-indigo-200'
            : 'hover:bg-slate-50 border border-transparent'
            }`}>
            <input
                type="checkbox"
                checked={selected}
                onChange={(e) => onSelect(file.id, e.target.checked, file)}
                className="w-3.5 h-3.5 rounded accent-indigo-600"
            />
            <File className={`w-3.5 h-3.5 ${selected ? 'text-indigo-600' : 'text-slate-400'}`} />
            <span className={`text-xs font-medium ${selected ? 'text-indigo-700 font-bold' : 'text-slate-600'}`}>
                {file.filename}
            </span>
        </label>
    );
};

export default TemplateSourcesPanel;
export { TEMPLATE_SOURCES };
