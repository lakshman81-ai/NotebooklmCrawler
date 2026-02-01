import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Zap, AlertCircle } from 'lucide-react';
import TemplateSourcesPanel, { TEMPLATE_SOURCES } from './TemplateSourcesPanel';
import FileUploadPanel from './FileUploadPanel';
import PromptOutputBox from './PromptOutputBox';
import StudyGuideOptions from './StudyGuideOptions';
import HandoutOptions from './HandoutOptions';
import { generatePromptForFile, generateReportPrompt, generateBasisSummary, generateSourcePromptsOnly } from './promptGenerator';
import { templateService } from '../../services/templateService';

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

    // State for study guide and handout options
    const [studyGuideOptions, setStudyGuideOptions] = useState({});
    const [handoutOptions, setHandoutOptions] = useState({});
    const [manualStudyGuide, setManualStudyGuide] = useState('');
    const [manualHandout, setManualHandout] = useState('');

    // State for final report
    const [reportOutput, setReportOutput] = useState('');
    const [basisSummary, setBasisSummary] = useState('');
    const [sourcePrompts, setSourcePrompts] = useState('');
    const [editableOutput, setEditableOutput] = useState('');
    const [copiedReport, setCopiedReport] = useState(false);
    const [copiedBasis, setCopiedBasis] = useState(false);
    const [copiedSource, setCopiedSource] = useState(false);

    // State for error messages
    const [errorMessage, setErrorMessage] = useState(null);

    // Settings from Dashboard context (would normally come from context provider)
    const [dashboardSettings, setDashboardSettings] = useState({
        grade: '',
        subject: '',
        topic: '',
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
        }
    });

    // Handle template source selection
    const handleSourceSelection = async (id, checked, fileInfo) => {
        const newSelected = new Set(selectedSources);
        const newData = new Map(selectedSourceData);

        if (checked) {
            newSelected.add(id);
            // Attempt to load file data
            const data = await loadTemplateFile(fileInfo.path);
            if (data) {
                newData.set(id, { ...fileInfo, data });
                generatePromptForSource(id, fileInfo, data);
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

    // Parse CSV content
    const parseCSV = (text) => {
        const lines = text.trim().split('\n');
        if (lines.length === 0) return [];

        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];

        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',');
            const row = {};
            headers.forEach((header, index) => {
                row[header] = values[index]?.trim() || '';
            });
            data.push(row);
        }

        return data;
    };

    // Generate placeholder data based on filename
    const generatePlaceholderData = (path) => {
        const filename = path.split('/').pop();

        if (filename.includes('ENGLISH') || filename.includes('MATH') || filename.includes('SKILL')) {
            return [
                { game_type: 'sample', question: 'Sample Question 1', answer: 'Answer 1', difficulty: 'Easy', category: 'test' },
                { game_type: 'sample', question: 'Sample Question 2', answer: 'Answer 2', difficulty: 'Medium', category: 'test' }
            ];
        } else if (filename.includes('biology') || filename.includes('chemistry') || filename.includes('physics') || filename.includes('math.xlsx')) {
            return [
                { Topic: 'Sample Topic', Concept: 'Key Concept', Details: 'Detailed information', Difficulty: 'Intermediate' }
            ];
        } else {
            return [
                { column1: 'sample data', column2: 'more data' }
            ];
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
                selected: false
            }];
        });
    };

    // Handle file upload
    const handleFileUpload = async (file) => {
        try {
            // Call backend API to parse file
            const result = await templateService.uploadFile(file);

            if (result.success) {
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
                        selected: false
                    }];
                });

                setErrorMessage(null);
            }
        } catch (error) {
            console.error('Upload error:', error);
            setErrorMessage(`Failed to upload file: ${error.message}`);
        }
    };

    // Handle file removal
    const handleFileRemove = () => {
        setUploadedFile(null);
        setGeneratedPrompts(prev => prev.filter(p => !p.id.startsWith('uploaded-')));
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

        const report = generateReportPrompt(
            selectedPromptData,
            studyGuideOptions,
            handoutOptions,
            manualStudyGuide,
            manualHandout,
            dashboardSettings
        );

        const summary = generateBasisSummary(
            selectedPromptData,
            studyGuideOptions,
            handoutOptions,
            dashboardSettings
        );

        const sources = generateSourcePromptsOnly(selectedPromptData);

        setReportOutput(report);
        setBasisSummary(summary);
        setSourcePrompts(sources);
        setEditableOutput(report);
        setErrorMessage(null);

        // Scroll to report
        setTimeout(() => {
            document.getElementById('report-output')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    // Copy to clipboard helpers
    const copyToClipboard = (text, setCopied) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="flex items-center gap-4 mb-4">
                <div className="p-3 bg-indigo-600 rounded-2xl text-white shadow-lg shadow-indigo-100">
                    <FileSpreadsheet className="w-7 h-7" />
                </div>
                <div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight">Templates</h2>
                    <p className="text-sm font-bold text-slate-500 uppercase tracking-wider mt-1">
                        Generate NotebookLM prompts from Excel files
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

            {/* Top Row: Template Sources + File Upload */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <TemplateSourcesPanel
                    selectedSources={selectedSources}
                    onSelectionChange={handleSourceSelection}
                />
                <FileUploadPanel
                    uploadedFile={uploadedFile}
                    onFileUpload={handleFileUpload}
                    onFileRemove={handleFileRemove}
                />
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
                                selected={prompt.selected}
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
            {reportOutput && (
                <div id="report-output" className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-[2rem] p-8 shadow-xl space-y-8">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-2xl font-black text-slate-800 flex items-center gap-3">
                            <FileSpreadsheet className="w-8 h-8 text-indigo-600" />
                            Generated Report
                        </h3>
                    </div>

                    {/* Input Basis - Read Only */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-black text-slate-500 uppercase tracking-widest">
                                Input Basis (Variables Preview)
                            </label>
                            <button
                                onClick={() => copyToClipboard(basisSummary, setCopiedBasis)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${copiedBasis
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-white text-indigo-700 hover:bg-indigo-100 shadow-sm border border-indigo-200'
                                    }`}
                            >
                                {copiedBasis ? '✓ Copied!' : '📋 Copy Basis'}
                            </button>
                        </div>
                        <textarea
                            readOnly
                            value={basisSummary}
                            className="w-full h-48 p-5 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-medium text-slate-700 resize-none focus:outline-none shadow-inner"
                        />
                        <p className="text-xs text-slate-400 italic pl-1">Summary of variables and selections used for generation</p>
                    </div>

                    {/* Input Prompts - Read Only */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-black text-slate-500 uppercase tracking-widest">
                                Source Input Prompts
                            </label>
                            <button
                                onClick={() => copyToClipboard(sourcePrompts, setCopiedSource)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${copiedSource
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : 'bg-white text-indigo-700 hover:bg-indigo-100 shadow-sm border border-indigo-200'
                                    }`}
                            >
                                {copiedSource ? '✓ Copied!' : '📋 Copy Sources'}
                            </button>
                        </div>
                        <textarea
                            readOnly
                            value={sourcePrompts}
                            className="w-full h-64 p-5 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-medium text-slate-700 resize-y focus:outline-none shadow-inner"
                        />
                        <p className="text-xs text-slate-400 italic pl-1">Consolidated prompts from all selected source files</p>
                    </div>

                    {/* Output Prompt - Editable */}
                    <div className="space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-black text-indigo-600 uppercase tracking-widest">
                                Final Output Prompt (Editable)
                            </label>
                            <button
                                onClick={() => copyToClipboard(editableOutput, setCopiedReport)}
                                className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black transition-all shadow-md ${copiedReport
                                    ? 'bg-emerald-500 text-white'
                                    : 'bg-indigo-600 text-white hover:bg-indigo-700 active:scale-95'
                                    }`}
                            >
                                {copiedReport ? '✓ Copied to Clipboard!' : '📋 Copy Final Prompt'}
                            </button>
                        </div>
                        <textarea
                            value={editableOutput}
                            onChange={(e) => setEditableOutput(e.target.value)}
                            className="w-full h-80 p-6 bg-white border-4 border-indigo-100 rounded-[2rem] text-base font-medium text-slate-800 resize-y focus:outline-none focus:border-indigo-400 shadow-xl"
                            placeholder="Edit the prompt as needed before copying..."
                        />
                        <p className="text-xs text-slate-500 font-bold italic pl-1">Edit this final synthesized prompt before pasting into NotebookLM</p>
                    </div>

                    <div className="bg-white border-2 border-indigo-100 rounded-[2rem] p-6 shadow-sm">
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
