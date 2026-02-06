import React, { useState, useEffect } from 'react';
import { Upload, File, X, CheckCircle } from 'lucide-react';

const FileUploadPanel = ({ uploadedFile, onFileUpload, onFileRemove }) => {
    const [dragActive, setDragActive] = useState(false);
    const [preview, setPreview] = useState('');

    useEffect(() => {
        if (uploadedFile && uploadedFile.data && uploadedFile.data.columns) {
            setPreview(uploadedFile.data.columns.join(', '));
        } else {
            setPreview('');
        }
    }, [uploadedFile]);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    };

    const handleFile = (file) => {
        // Validate file type
        const validTypes = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];
        const validExtensions = ['.csv', '.xlsx', '.xls'];
        const isValid = validTypes.includes(file.type) ||
            validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

        if (!isValid) {
            alert('Please upload a valid Excel (.xlsx, .xls) or CSV file');
            return;
        }

        onFileUpload(file);
    };

    return (
        <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-200 space-y-5 h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center gap-3 pb-4 border-b border-slate-100 flex-shrink-0">
                <div className="p-2 bg-emerald-50 rounded-xl">
                    <Upload className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                    <h3 className="text-base font-black text-slate-800">File Upload</h3>
                    <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Upload custom Excel/CSV files</p>
                </div>
            </div>

            {/* Upload Area */}
            {!uploadedFile ? (
                <div
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-all flex-grow flex flex-col items-center justify-center ${dragActive
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/50'
                        }`}
                >
                    <input
                        type="file"
                        id="file-upload"
                        accept=".xlsx,.xls,.csv"
                        onChange={handleChange}
                        className="hidden"
                    />

                    <div className="flex flex-col items-center gap-4">
                        <div className="p-4 bg-white rounded-2xl shadow-sm">
                            <Upload className="w-8 h-8 text-indigo-600" />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-slate-700 mb-1">
                                Drag and drop your Excel file here
                            </p>
                            <p className="text-xs text-slate-500">or</p>
                        </div>
                        <label
                            htmlFor="file-upload"
                            className="px-6 py-3 bg-indigo-600 text-white rounded-xl text-sm font-black uppercase tracking-wider cursor-pointer hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-100"
                        >
                            Upload Excel File
                        </label>
                        <p className="text-[10px] text-slate-400 font-medium">
                            Supported: .xlsx, .xls, .csv
                        </p>
                    </div>
                </div>
            ) : (
                /* Uploaded File Display + Preview */
                <div className="flex flex-col h-full space-y-4">
                    <div className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-2xl p-5 flex-shrink-0">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-emerald-500 rounded-xl text-white shadow-lg">
                                <File className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-bold text-slate-800 truncate">
                                            {uploadedFile.name}
                                        </p>
                                        <p className="text-xs text-slate-600 mt-1">
                                            {(uploadedFile.size / 1024).toFixed(2)} KB
                                        </p>
                                    </div>
                                    <button
                                        onClick={onFileRemove}
                                        className="p-2 rounded-lg hover:bg-red-100 text-slate-400 hover:text-red-600 transition-all"
                                        title="Remove file"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                                <div className="flex items-center gap-2 mt-3">
                                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                                    <span className="text-xs font-bold text-emerald-700">File uploaded successfully</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Unified Preview for Uploaded File */}
                    <div className="flex-grow flex flex-col min-h-0 space-y-1">
                        <label className="text-[10px] font-bold text-slate-400 uppercase">Structure Preview (Editable)</label>
                        <textarea
                            value={preview}
                            onChange={(e) => setPreview(e.target.value)}
                            className="w-full flex-grow p-3 bg-slate-50 border border-slate-200 rounded-xl text-[10px] font-mono text-slate-600 focus:outline-none focus:border-emerald-500 resize-none min-h-[100px]"
                            placeholder="Column headers will appear here..."
                        />
                        <p className="text-[10px] text-slate-400 italic">These headers will be used to guide prompt generation.</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FileUploadPanel;
