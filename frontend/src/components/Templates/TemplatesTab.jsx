import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Zap, AlertCircle, Copy, CheckCircle, Info } from 'lucide-react';
import TemplateSourcesPanel, { TEMPLATE_SOURCES } from './TemplateSourcesPanel';
import FileUploadPanel from './FileUploadPanel';
import ExternalSourcePanel from './ExternalSourcePanel';
import PromptOutputBox from './PromptOutputBox';
import StudyGuideOptions from './StudyGuideOptions';
import HandoutOptions from './HandoutOptions';
import { generatePromptForFile, generateReportPrompt, generateJulesPrompt } from './promptGenerator';
import { templateService } from '../../services/templateService';
import { logGate } from '../../services/loggingService';

// --- Persistence Helpers ---
const serializeState = (state) => {
    return JSON.stringify({
        selectedSources: Array.from(state.selectedSources),
        selectedSourceData: Array.from(state.selectedSourceData.entries()),
        selectedPrompts: Array.from(state.selectedPrompts),
        generatedPrompts: state.generatedPrompts
    });
};

const deserializeState = (json) => {
    try {
        const obj = JSON.parse(json);
        return {
            selectedSources: new Set(obj.selectedSources),
            selectedSourceData: new Map(obj.selectedSourceData),
            selectedPrompts: new Set(obj.selectedPrompts),
            generatedPrompts: obj.generatedPrompts
        };
    } catch (e) {
        console.error("Error deserializing state", e);
        return null;
    }
};

/**
 * Main Templates Tab Component
 * Generates NotebookLM prompts from Excel/CSV template files
 */
const TemplatesTab = () => {
    // State for file selections
    const [selectedSources, setSelectedSources] = useState(new Set());
    const [selectedSourceData, setSelectedSourceData] = useState(new Map());
    const [uploadedFile, setUploadedFile] = useState(null);

    // State for generated prompts
    const [generatedPrompts, setGeneratedPrompts] = useState([]);
    const [selectedPrompts, setSelectedPrompts] = useState(new Set());

    // State for update feedback
    const [promptsRefreshed, setPromptsRefreshed] = useState(false);

    // State for study guide and handout options
    const [studyGuideOptions, setStudyGuideOptions] = useState({});
    const [handoutOptions, setHandoutOptions] = useState({});
    const [manualStudyGuide, setManualStudyGuide] = useState('');
    const [manualHandout, setManualHandout] = useState('');

    // State for final report
    const [reportBasis, setReportBasis] = useState('');
    const [inputPrompts, setInputPrompts] = useState('');
    const [outputPrompt, setOutputPrompt] = useState('');
    const [julesPrompt, setJulesPrompt] = useState('');
    const [copiedInput, setCopiedInput] = useState(false);
    const [copiedOutput, setCopiedOutput] = useState(false);
    const [copiedJules, setCopiedJules] = useState(false);

    // State for error messages
    const [errorMessage, setErrorMessage] = useState(null);

    // Settings from Dashboard context
    const [dashboardSettings, setDashboardSettings] = useState({
        grade: '',
        subject: '',
        topic: '',
        subtopics: '',
        difficulty: 'Connect',
        outputs: {
            studyGuide: true,
            quiz: true,
            handout: false
        },
        quizConfig: {
            mcq: 10,
            ar: 5,
            detailed: 3,
            custom: ''
        },
        keywordsScrape: '',
        keywordsReport: '',
        targetUrls: ''
    });

    // Unified Initialization Effect (Load Config + Load State + Regenerate)
    useEffect(() => {
        const init = async () => {
            // 1. Load Dashboard Settings
            let currentSettings = { ...dashboardSettings };
            const savedContext = localStorage.getItem('dashboard_context');
            if (savedContext) {
                try {
                    const parsed = JSON.parse(savedContext);
                    currentSettings = {
                        grade: parsed.grade || currentSettings.grade,
                        subject: parsed.subject || currentSettings.subject,
                        topic: parsed.topic || currentSettings.topic,
                        subtopics: parsed.subtopics || currentSettings.subtopics,
                        difficulty: parsed.difficulty || currentSettings.difficulty,
                        outputs: parsed.outputs || currentSettings.outputs,
                        quizConfig: parsed.quizConfig || currentSettings.quizConfig,
                        keywordsScrape: parsed.keywordsScrape || currentSettings.keywordsScrape,
                        keywordsReport: parsed.keywordsReport || currentSettings.keywordsReport,
                        targetUrls: parsed.targetUrls || currentSettings.targetUrls
                    };
                    setDashboardSettings(currentSettings);
                } catch (e) {
                    console.error('Failed to load dashboard context:', e);
                }
            }

            // 2. Load Persisted Tab State
            const savedState = localStorage.getItem('templates_tab_state');
            if (savedState) {
                const state = deserializeState(savedState);
                if (state) {
                    // 3. Regenerate prompts using current dashboard settings
                    // This ensures prompts are up-to-date even if settings changed in another tab
                    const refreshedPrompts = state.generatedPrompts.map(p => {
                        const fileInfo = state.selectedSourceData.get(p.id);
                        // If we have data, regenerate. If not (e.g. data lost), keep old prompt?
                        // Or if data missing, we can't regenerate.
                        // With local persistence of 'selectedSourceData', we should have it.
                        if (fileInfo && fileInfo.data) {
                            const newPromptText = generatePromptForFile(fileInfo.data, fileInfo.filename, p.source, currentSettings);
                            return { ...p, prompt: newPromptText };
                        }
                        return p;
                    });

                    setSelectedSources(state.selectedSources);
                    setSelectedSourceData(state.selectedSourceData);
                    setSelectedPrompts(state.selectedPrompts);
                    setGeneratedPrompts(refreshedPrompts);

                    if (refreshedPrompts.length > 0) {
                         setPromptsRefreshed(true);
                         setTimeout(() => setPromptsRefreshed(false), 4000);
                    }
                }
            }
        };
        init();
    }, []);

    // Persistence Effect
    useEffect(() => {
        const state = {
            selectedSources,
            selectedSourceData,
            selectedPrompts,
            generatedPrompts
        };
        try {
            localStorage.setItem('templates_tab_state', serializeState(state));
        } catch (e) {
            console.warn("Failed to persist templates state (quota exceeded?)", e);
        }
    }, [selectedSources, selectedSourceData, selectedPrompts, generatedPrompts]);


    // Handle template source selection
    const handleSourceSelection = async (id, checked, fileInfo) => {
        logGate('TemplatesTab', 'SELECT:SOURCE', { id, checked, fileInfo });
        const newSelected = new Set(selectedSources);
        const newData = new Map(selectedSourceData);

        if (checked) {
            // Attempt to load file data
            const data = await loadTemplateFile(fileInfo.path);
            if (data) {
                newSelected.add(id);
                newData.set(id, { ...fileInfo, data });
                generatePromptForSource(id, fileInfo, data);
            } else {
                logGate('TemplatesTab', 'SELECT:SOURCE:FAIL', { id, error: 'Failed to load data' });
            }
        } else {
            newSelected.delete(id);
            newData.delete(id);
            // Remove generated prompt
            setGeneratedPrompts(prev => prev.filter(p => p.id !== id));
            // Remove from selected prompts
            setSelectedPrompts(prev => {
                const updated = new Set(prev);
                updated.delete(id);
                return updated;
            });
        }

        setSelectedSources(newSelected);
        setSelectedSourceData(newData);
    };

    // Handle structure update (editable headers from TemplateSourcesPanel)
    const handleStructureUpdate = (id, newStructureString) => {
        logGate('TemplatesTab', 'UPDATE:STRUCTURE', { id, newStructureString });

        const currentData = selectedSourceData.get(id);
        if (!currentData || !currentData.data) return;

        // Parse headers
        const newHeaders = newStructureString.split(',').map(h => h.trim()).filter(h => h);

        // Update local data state
        const updatedDataPayload = {
            ...currentData.data,
            columns: newHeaders
        };

        const updatedFileInfo = {
            ...currentData,
            data: updatedDataPayload
        };

        const newData = new Map(selectedSourceData);
        newData.set(id, updatedFileInfo);
        setSelectedSourceData(newData);

        // Regenerate prompt with new headers
        generatePromptForSource(id, updatedFileInfo, updatedDataPayload);
    };

    // Load template file (Excel/CSV from backend)
    const loadTemplateFile = async (path) => {
        try {
            // Call backend API to read actual file
            const result = await templateService.readTemplateFile(path);

            if (result.success) {
                setErrorMessage(null);
                return {
                    columns: result.columns,
                    rowCount: result.rowCount,
                    sampleData: result.sampleData,
                    sheets: result.sheets || [],
                    columnTypes: result.columnTypes || {},
                    filename: result.filename
                };
            }

            return null;
        } catch (error) {
            console.error('Error loading template:', error);
            setErrorMessage(`Failed to load template: ${error.message}`);
            return null;
        }
    };

    // Generate prompt for a selected source
    const generatePromptForSource = (id, fileInfo, data) => {
        const source = fileInfo.path.startsWith('Kani') ? 'Kani' : 'Harshitha';
        const prompt = generatePromptForFile(data, fileInfo.filename, source, dashboardSettings);

        setGeneratedPrompts(prev => {
            // Remove existing prompt for this file if any
            const filtered = prev.filter(p => p.id !== id);
            return [...filtered, {
                id,
                filename: fileInfo.filename,
                prompt,
                source,
                selected: true // Auto-select by default
            }];
        });

        // Auto-select in state too
        setSelectedPrompts(prev => {
            const updated = new Set(prev);
            updated.add(id);
            return updated;
        });
    };

    // Handle file upload
    const handleFileUpload = async (file) => {
        try {
            logGate('TemplatesTab', 'UPLOAD:START', { filename: file.name, size: file.size });
            // Call backend API to parse file
            const result = await templateService.uploadFile(file);

            if (result.success) {
                logGate('TemplatesTab', 'UPLOAD:SUCCESS', { filename: result.filename });
                const fileData = {
                    columns: result.columns,
                    rowCount: result.rowCount,
                    sampleData: result.sampleData,
                    columnTypes: result.columnTypes || {},
                    filename: result.filename
                };

                setUploadedFile({
                    name: file.name,
                    size: file.size,
                    data: fileData
                });

                // Generate prompt for uploaded file
                const uploadId = `uploaded-${file.name}`;
                const prompt = generatePromptForFile(fileData, file.name, 'Uploaded', dashboardSettings);

                setGeneratedPrompts(prev => {
                    const filtered = prev.filter(p => !p.id.startsWith('uploaded-'));
                    return [...filtered, {
                        id: uploadId,
                        filename: `Uploaded: ${file.name}`,
                        prompt,
                        source: 'Uploaded',
                        selected: true // Auto-select
                    }];
                });

                setSelectedPrompts(prev => {
                     const updated = new Set(prev);
                     updated.add(uploadId);
                     return updated;
                });

                setErrorMessage(null);
            }
        } catch (error) {
            console.error('Upload error:', error);
            logGate('TemplatesTab', 'UPLOAD:ERROR', { error: error.message });
            setErrorMessage(`Failed to upload file: ${error.message}`);
        }
    };

    // Handle file removal
    const handleFileRemove = () => {
        setUploadedFile(null);
        setGeneratedPrompts(prev => prev.filter(p => !p.id.startsWith('uploaded-')));
        // Also remove from selected prompts?
        // Logic gets complex to find the ID. Assuming uploadId format.
        // We'll leave it in selectedPrompts, it won't be found in generatedPrompts so it filters out on report gen.
    };

    // Handle external source addition
    const handleExternalSourceAdd = (data) => {
        logGate('TemplatesTab', 'ADD:EXTERNAL', { url: data.filename });

        // Use the manually refined structure (headers only) for the prompt
        const prompt = `# Source Context: ${data.filename} (External)\n` +
                       `**Source Origin:** External URL\n` +
                       `**Schema Definition (Editable):**\n${data.structure}\n\n` +
                       `**Instruction:** Analyze content based on the above schema.`;

        setGeneratedPrompts(prev => {
            const filtered = prev.filter(p => p.id !== data.id);
            return [...filtered, {
                id: data.id,
                filename: `External: ${data.filename.split('/').pop() || 'URL'}`,
                prompt: prompt,
                source: 'External',
                selected: true
            }];
        });

        setSelectedPrompts(prev => {
             const updated = new Set(prev);
             updated.add(data.id);
             return updated;
        });
    };

    // Handle prompt selection
    const handlePromptSelection = (id, checked) => {
        setSelectedPrompts(prev => {
            const updated = new Set(prev);
            if (checked) {
                updated.add(id);
            } else {
                updated.delete(id);
            }
            return updated;
        });

        // Update the generated prompts selected state
        setGeneratedPrompts(prev =>
            prev.map(p => p.id === id ? { ...p, selected: checked } : p)
        );
    };

    // Generate final report
    const handleGenerateReport = () => {
        const selectedPromptData = generatedPrompts.filter(p => selectedPrompts.has(p.id));
        logGate('TemplatesTab', 'GENERATE:REPORT', {
            selectedCount: selectedPromptData.length,
            settings: dashboardSettings
        });
        const { basis, inputPrompts, outputPrompt } = generateReportPrompt(
            selectedPromptData,
            studyGuideOptions,
            handoutOptions,
            manualStudyGuide,
            manualHandout,
            dashboardSettings
        );

        setReportBasis(basis);
        setInputPrompts(inputPrompts);
        setOutputPrompt(outputPrompt);
        setJulesPrompt(generateJulesPrompt(inputPrompts));
        setErrorMessage(null);

        // Scroll to report
        setTimeout(() => {
            document.getElementById('report-output')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    // Copy input prompts to clipboard
    const copyInputPrompts = () => {
        navigator.clipboard.writeText(inputPrompts);
        setCopiedInput(true);
        setTimeout(() => setCopiedInput(false), 2000);
    };

    // Copy final output prompt to clipboard
    const copyOutputPrompt = () => {
        navigator.clipboard.writeText(outputPrompt);
        setCopiedOutput(true);
        setTimeout(() => setCopiedOutput(false), 2000);
    };

    // Copy Jules prompt to clipboard
    const copyJulesPrompt = () => {
        navigator.clipboard.writeText(julesPrompt);
        setCopiedJules(true);
        setTimeout(() => setCopiedJules(false), 2000);
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-indigo-600 rounded-2xl text-white shadow-lg shadow-indigo-100">
                    <FileSpreadsheet className="w-7 h-7" />
                </div>
                <div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Prompt Generator</h2>
                    <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mt-1">
                        Generate NotebookLM and Jules prompts from sources
                    </p>
                </div>
            </div>

            {/* Error Message Display */}
            {errorMessage && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-4 flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1 flex justify-between items-start gap-4">
                        <div>
                            <p className="text-sm font-bold text-red-900 mb-1">Error</p>
                            <p className="text-xs text-red-700">{errorMessage}</p>
                        </div>
                        <button
                            onClick={() => setErrorMessage(null)}
                            className="text-red-600 hover:text-red-700 font-bold text-xs flex-shrink-0"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            {/* Success/Refreshed Banner */}
            {promptsRefreshed && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-start gap-3 animate-in slide-in-from-top-2">
                    <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <p className="text-sm font-bold text-emerald-900 mb-1">Prompts Updated</p>
                        <p className="text-xs text-emerald-700">
                            Generated prompts have been refreshed to match your latest Dashboard settings.
                        </p>
                    </div>
                </div>
            )}

            {/* Info Banner */}
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                    <p className="text-sm font-bold text-amber-900 mb-1">Template Integration with Dashboard Settings</p>
                    <p className="text-xs text-amber-700">
                        Prompts are generated using current Dashboard settings (difficulty: <strong>{dashboardSettings.difficulty}</strong>,
                        outputs: <strong>{Object.entries(dashboardSettings.outputs).filter(([k, v]) => v).map(([k]) => k).join(', ')}</strong>).
                        Customize settings in the Dashboard Configuration section.
                    </p>
                </div>
            </div>

            {/* Top Row: Template Sources + File Upload + External */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1 h-full">
                    <TemplateSourcesPanel
                        selectedSources={selectedSources}
                        selectedSourceData={selectedSourceData}
                        onSelectionChange={handleSourceSelection}
                        onUpdateStructure={handleStructureUpdate}
                    />
                </div>
                <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6 h-fit">
                    <FileUploadPanel
                        uploadedFile={uploadedFile}
                        onFileUpload={handleFileUpload}
                        onFileRemove={handleFileRemove}
                    />
                    <ExternalSourcePanel onAddPrompt={handleExternalSourceAdd} />
                </div>
            </div>

            {/* Generated Prompts Grid */}
            {generatedPrompts.length > 0 && (
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-black text-slate-800">Generated Prompts</h3>
                        <p className="text-xs font-bold text-slate-500">
                            {selectedPrompts.size} of {generatedPrompts.length} selected
                        </p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {generatedPrompts.map(prompt => (
                            <PromptOutputBox
                                key={prompt.id}
                                id={prompt.id}
                                filename={prompt.filename}
                                prompt={prompt.prompt}
                                selected={prompt.selected} // Should rely on selectedPrompts set?
                                // Actually PromptOutputBox takes selected boolean.
                                // We are passing prompt.selected which we updated in state.
                                onSelect={handlePromptSelection}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Options Row: Study Guide + Handout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <StudyGuideOptions
                    selectedOptions={studyGuideOptions}
                    onOptionChange={(id, checked) => setStudyGuideOptions(prev => ({ ...prev, [id]: checked }))}
                    manualEntry={manualStudyGuide}
                    onManualEntryChange={setManualStudyGuide}
                />
                <HandoutOptions
                    selectedOptions={handoutOptions}
                    onOptionChange={(id, checked) => setHandoutOptions(prev => ({ ...prev, [id]: checked }))}
                    manualEntry={manualHandout}
                    onManualEntryChange={setManualHandout}
                />
            </div>

            {/* Generate Button */}
            <div className="flex justify-center pt-4">
                <button
                    onClick={handleGenerateReport}
                    className="flex items-center gap-3 px-12 py-5 rounded-2xl font-black text-sm uppercase tracking-[0.2em] transition-all shadow-2xl bg-indigo-600 text-white shadow-indigo-100 hover:bg-indigo-500 active:scale-95 cursor-pointer"
                >
                    <Zap className="w-5 h-5" />
                    Generate Report Prompts
                </button>
            </div>

            {/* Report Output */}
            {reportBasis && (
                <div id="report-output" className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-[2rem] p-8 shadow-xl space-y-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xl font-black text-slate-800 flex items-center gap-3">
                            <FileSpreadsheet className="w-6 h-6 text-indigo-600" />
                            Generated Report
                        </h3>
                    </div>

                    {/* Input Basis - Read Only */}
                    <div className="space-y-2">
                        <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                            Input Basis (Read-only Preview of Variables)
                        </label>
                        <textarea
                            readOnly
                            value={reportBasis}
                            className="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-xl text-sm font-sans text-slate-700 resize-none focus:outline-none"
                        />
                        <p className="text-[10px] text-slate-400 italic">Summary of variables and settings used for generation</p>
                    </div>

                    {/* Source Input Prompts - Editable with Copy */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                                Notebooklm Input Prompt(Editable)
                            </label>
                            <button
                                onClick={copyInputPrompts}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${copiedInput
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-white text-indigo-700 hover:bg-indigo-100 shadow-sm border border-indigo-200'
                                    }`}
                            >
                                {copiedInput ? '✓ Copied!' : <span className="flex items-center gap-1"><Copy className="w-3 h-3" /> Copy</span>}
                            </button>
                        </div>
                        <textarea
                            value={inputPrompts}
                            onChange={(e) => setInputPrompts(e.target.value)}
                            className="w-full h-56 p-4 bg-white border-2 border-indigo-300 rounded-xl text-sm font-mono text-slate-700 resize-y focus:outline-none focus:border-indigo-500"
                            placeholder="Individual source prompts..."
                        />
                        <p className="text-[10px] text-slate-400 italic">Prompts generated for each selected file</p>
                    </div>

                    {/* Output Prompt - Editable */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                                Notebooklm Output Prompt(Editable)
                            </label>
                            <button
                                onClick={copyOutputPrompt}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${copiedOutput
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-white text-indigo-700 hover:bg-indigo-100 shadow-sm border border-indigo-200'
                                    }`}
                            >
                                {copiedOutput ? '✓ Copied!' : <span className="flex items-center gap-1"><Copy className="w-3 h-3" /> Copy</span>}
                            </button>
                        </div>
                        <textarea
                            value={outputPrompt}
                            onChange={(e) => setOutputPrompt(e.target.value)}
                            className="w-full h-56 p-4 bg-white border-2 border-indigo-300 rounded-xl text-sm font-mono text-slate-700 resize-y focus:outline-none focus:border-indigo-500"
                            placeholder="Edit the final prompt as needed before copying..."
                        />
                        <p className="text-[10px] text-slate-400 italic">Edit this prompt before copying to NotebookLM</p>
                    </div>

                    {/* Jules Prompt - Editable */}
                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <label className="text-xs font-black text-slate-500 uppercase tracking-widest">
                                Jules Prompt (Editable)
                            </label>
                            <button
                                onClick={copyJulesPrompt}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${copiedJules
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-white text-indigo-700 hover:bg-indigo-100 shadow-sm border border-indigo-200'
                                    }`}
                            >
                                {copiedJules ? '✓ Copied!' : <span className="flex items-center gap-1"><Copy className="w-3 h-3" /> Copy</span>}
                            </button>
                        </div>
                        <textarea
                            value={julesPrompt}
                            onChange={(e) => setJulesPrompt(e.target.value)}
                            className="w-full h-56 p-4 bg-white border-2 border-indigo-300 rounded-xl text-sm font-mono text-slate-700 resize-y focus:outline-none focus:border-indigo-500"
                            placeholder="Prompt for Jules..."
                        />
                        <p className="text-[10px] text-slate-400 italic">Optimized prompt for Jules based on the input context</p>
                    </div>

                    <div className="bg-indigo-100 border border-indigo-200 rounded-xl p-4">
                        <p className="text-xs font-bold text-indigo-900 mb-2">📝 Next Steps:</p>
                        <ol className="text-xs text-indigo-800 space-y-1 list-decimal list-inside">
                            <li>Edit the Output Prompt above if needed</li>
                            <li>Copy using the button above</li>
                            <li>Open NotebookLM → "Notebook guide" → "Create Your Own"</li>
                            <li>Paste and click Generate</li>
                        </ol>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TemplatesTab;
