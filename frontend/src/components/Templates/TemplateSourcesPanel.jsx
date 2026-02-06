import React, { useState, useEffect } from 'react';
import { FolderOpen, ChevronDown, ChevronRight, File, RefreshCw, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../../services/apiConfig';

/**
 * Template file structure (Nested)
 * Now loaded dynamically from templates.json or via API
 */
let TEMPLATE_SOURCES = {};

/**
 * Recursive Tree Component
 */
const FileTree = ({ data, parentPath = '', level = 0, selectedSources, onSelectionChange, expanded, toggleExpand }) => {
    // If array, it's a list of files (Leaf Nodes)
    if (Array.isArray(data)) {
        return (
            <div className={`ml-4 space-y-1 border-l border-slate-100 pl-2`}>
                {data.map(file => (
                    <FileCheckbox
                        key={file.id}
                        file={file}
                        selected={selectedSources.has(file.id)}
                        onSelect={onSelectionChange}
                    />
                ))}
            </div>
        );
    }

    // Otherwise, iterate keys (Folder Nodes)
    return (
        <div className={`space-y-1 ${level > 0 ? 'ml-4 border-l border-slate-100 pl-2' : ''}`}>
            {Object.entries(data).map(([folderName, content]) => {
                const currentPath = parentPath ? `${parentPath}-${folderName}` : folderName;
                const isExpanded = expanded.has(currentPath);

                // Helper to get all files in this subtree for "Select All" logic
                const getAllFiles = (node) => {
                    if (Array.isArray(node)) return node;
                    return Object.values(node).flatMap(getAllFiles);
                };
                const filesInFolder = getAllFiles(content);
                const hasFiles = filesInFolder.length > 0;
                const allSelected = hasFiles && filesInFolder.every(f => selectedSources.has(f.id));

                return (
                    <div key={currentPath}>
                        <div
                            className={`flex items-center justify-between p-2 rounded-lg cursor-pointer transition-all ${isExpanded ? 'bg-slate-50' : 'hover:bg-slate-50'
                                }`}
                            onClick={(e) => { e.stopPropagation(); toggleExpand(currentPath); }}
                        >
                            <div className="flex items-center gap-2">
                                {isExpanded ? (
                                    <ChevronDown className="w-4 h-4 text-slate-400" />
                                ) : (
                                    <ChevronRight className="w-4 h-4 text-slate-400" />
                                )}
                                <FolderOpen className={`w-4 h-4 ${level === 0 ? 'text-amber-500' : 'text-indigo-500'}`} />
                                <span className="text-sm font-bold text-slate-700">{folderName}</span>
                                <span className="text-xs text-slate-400 font-medium">({filesInFolder.length})</span>
                            </div>

                            {hasFiles && (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        filesInFolder.forEach(file => onSelectionChange(file.id, !allSelected, file));
                                    }}
                                    className="text-[10px] font-bold text-indigo-600 hover:text-indigo-700 px-2 py-1 rounded hover:bg-indigo-100 transition-colors"
                                >
                                    {allSelected ? 'None' : 'All'}
                                </button>
                            )}
                        </div>

                        {isExpanded && (
                            <FileTree
                                data={content}
                                parentPath={currentPath}
                                level={level + 1}
                                selectedSources={selectedSources}
                                onSelectionChange={onSelectionChange}
                                expanded={expanded}
                                toggleExpand={toggleExpand}
                            />
                        )}
                    </div>
                );
            })}
        </div>
    );
};

const TemplateSourcesPanel = ({ selectedSources, onSelectionChange }) => {
    // State for template data
    const [templateData, setTemplateData] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Initial State: Expand top-level folders
    const [expandedSections, setExpandedSections] = useState(new Set(['Kani', 'Harshitha']));

    // Load templates on mount (Cached)
    useEffect(() => {
        const loadCachedTemplates = async () => {
            try {
                // Try fetching the cached file from public directory
                // Note: In Vite dev, public/ is at root. In prod, it's at root.
                // We use a timestamp to avoid browser caching of the file itself if needed,
                // but user asked for "do once", so maybe standard caching is fine.
                // However, "fetch only if user clicks refresh" implies we trust the file until refreshed.
                const response = await fetch('/templates.json');
                if (response.ok) {
                    const data = await response.json();
                    setTemplateData(data);
                    TEMPLATE_SOURCES = data; // Update export if needed
                    // Auto-expand top level keys
                    setExpandedSections(new Set(Object.keys(data)));
                } else {
                    // Cache missing, trigger initial refresh
                    console.log("Template cache missing, triggering refresh...");
                    handleRefresh();
                }
            } catch (err) {
                console.warn("Failed to load template cache", err);
                // Fallback to initial refresh
                handleRefresh();
            }
        };
        loadCachedTemplates();
    }, []);

    const handleRefresh = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_BASE_URL}/api/templates/refresh`, { method: 'POST' });
            if (!res.ok) throw new Error("Failed to refresh templates");

            const result = await res.json();
            setTemplateData(result.tree);
            TEMPLATE_SOURCES = result.tree;
            setExpandedSections(new Set(Object.keys(result.tree)));
        } catch (e) {
            console.error("Template refresh error:", e);
            setError("Failed to load templates. Is backend running?");
        } finally {
            setLoading(false);
        }
    };

    const toggleExpand = (path) => {
        setExpandedSections(prev => {
            const next = new Set(prev);
            if (next.has(path)) {
                next.delete(path);
            } else {
                next.add(path);
            }
            return next;
        });
    };

    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-5 h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 flex-shrink-0">
                <div className="flex items-center gap-3">
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
                <button
                    onClick={handleRefresh}
                    disabled={loading}
                    className="p-2 hover:bg-slate-100 rounded-full transition-colors disabled:opacity-50 text-slate-500 hover:text-indigo-600"
                    title="Refresh Templates"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                </button>
            </div>

            {error && (
                <div className="p-3 bg-red-50 text-red-600 text-xs rounded-lg">
                    {error}
                </div>
            )}

            {/* File Tree - Scrollable Area */}
            <div className="space-y-2 overflow-y-auto custom-scrollbar pr-2 flex-grow min-h-[300px]">
                {Object.keys(templateData).length === 0 && !loading && !error ? (
                    <div className="text-center py-10 text-slate-400 text-sm">
                        No templates found. <br/> Click refresh to scan.
                    </div>
                ) : (
                    <FileTree
                        data={templateData}
                        selectedSources={selectedSources}
                        onSelectionChange={onSelectionChange}
                        expanded={expandedSections}
                        toggleExpand={toggleExpand}
                    />
                )}
            </div>

            {/* Footer Stats */}
            <div className="pt-4 border-t border-slate-100 flex-shrink-0">
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
                className="w-3.5 h-3.5 rounded accent-indigo-600 cursor-pointer"
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
