/**
 * Prompt Generator Utility for Templates Tab
 * Generates NotebookLM prompts based on file content and settings
 */

/**
 * Analyzes CSV/Excel data structure
 * @param {Array} data - Parsed data rows
 * @param {string} filename - Source filename
 * @returns {Object} - Analyzed structure
 */
export function analyzeFileStructure(data, filename) {
    if (!data || data.length === 0) {
        return { columns: [], rowCount: 0, contentType: 'unknown' };
    }

    const columns = Object.keys(data[0] || {});
    const rowCount = data.length;

    // Detect content type based on columns
    let contentType = 'unknown';
    const columnSet = new Set(columns.map(c => c.toLowerCase()));

    if (columnSet.has('game_type') || columnSet.has('question') || columnSet.has('answer')) {
        contentType = 'quiz';
    } else if (columnSet.has('topic') || columnSet.has('subject')) {
        contentType = 'study_material';
    } else if (columnSet.has('difficulty') || columnSet.has('category')) {
        contentType = 'educational_content';
    }

    return { columns, rowCount, contentType };
}

/**
 * Generate a NotebookLM prompt for a single file
 * @param {Array} fileData - Parsed file data
 * @param {string} filename - Source filename
 * @param {string} source - Source category (Kani/Harshitha)
 * @param {Object} settings - Settings from Dashboard (difficulty, outputs, etc.)
 * @returns {string} - Generated prompt
 */
export function generatePromptForFile(fileData, filename, source, settings = {}) {
    // Destructure expanded fields from backend
    const { columns, rowCount, sampleData, sheets, columnTypes } = fileData;
    const structure = analyzeFileStructure(fileData.sampleData || [], filename);
    const contentType = structure.contentType;

    // Extract subject from filename
    const subject = extractSubjectFromFilename(filename);

    let prompt = `# NotebookLM Prompt - ${filename}\n\n`;
    prompt += `**Source:** ${source}\n`;
    prompt += `**Records:** ${rowCount} items\n\n`;

    // Excel/CSV Format Details
    prompt += `## Excel/CSV Input Format\n`;
    prompt += `**File Structure:**\n`;
    prompt += `- **Format:** ${filename.endsWith('.csv') ? 'CSV' : 'Excel (.xlsx)'}\n`;
    prompt += `- **Sheets:** ${sheets?.length > 0 ? sheets.join(', ') : 'Single sheet'}\n`;
    prompt += `- **Headers (Row 1):** ${columns.join(', ')}\n`;
    prompt += `- **Data Rows:** ${rowCount} total records\n\n`;

    // Column Data Types
    if (columnTypes && Object.keys(columnTypes).length > 0) {
        prompt += `**Column Data Types:**\n`;
        Object.entries(columnTypes).forEach(([col, type]) => {
            prompt += `- ${col}: ${type}\n`;
        });
        prompt += `\n`;
    }

    prompt += `**Expected Output Format (CRITICAL):**\n`;
    prompt += `- Provide output in a valid CSV code block.\n`;
    prompt += `- Use EXACTLY these headers in the first row: ${columns.join(',')}\n`;
    prompt += `- Do not add, remove, or rename any columns.\n`;
    prompt += `- Use commas as separators. Wrap any field containing commas in double quotes.\n`;
    prompt += `- Do not include any introductory or concluding text outside the code block for the CSV data.\n`;
    prompt += `- Preserve data relationships from the source.\n\n`;

    // Add input context
    prompt += `## Source Data Structure\n`;
    prompt += `Required Columns: ${columns.join(', ')}\n\n`;

    // Add difficulty context from settings
    if (settings.difficulty) {
        const diffMap = {
            'Identify': 'Focus on definitions, basic facts, and identification of key terms. (Easy Level)',
            'Connect': 'Focus on relationships, cause-and-effect, and connecting concepts. (Medium Level)',
            'Extend': 'Focus on applications, scenario-based analysis, and extending concepts. (Hard Level)'
        };
        prompt += `## Difficulty Level\n`;
        prompt += `${settings.difficulty}: ${diffMap[settings.difficulty] || diffMap['Connect']}\n\n`;
    }

    // Content-specific instructions
    if (contentType === 'quiz' || contentType === 'educational_content' || (sampleData && sampleData.length > 0)) {
        prompt += `## Content Instructions\n`;
        prompt += `This file contains ${contentType === 'quiz' ? 'quiz questions and answers' : 'educational content'} `;
        prompt += `for ${subject || 'general topics'}.\n\n`;

        if (sampleData && sampleData.length > 0) {
            prompt += `**Sample Data (First ${sampleData.length} rows):**\n`;
            sampleData.forEach((row, idx) => {
                prompt += `Row ${idx + 1}:\n`;
                Object.entries(row).forEach(([key, value]) => {
                    if (value && String(value).length < 200) {
                        prompt += `  - ${key}: ${value}\n`;
                    }
                });
                prompt += `\n`;
            });
        }
    }

    // Add output instructions based on settings
    if (settings.outputs) {
        prompt += `## Requested Outputs\n`;
        if (settings.outputs.studyGuide) {
            prompt += `- **Study Guide**: Create a comprehensive study guide extracting key concepts, definitions, and important information.\n`;
        }
        if (settings.outputs.quiz && settings.quizConfig) {
            const q = settings.quizConfig;
            prompt += `- **Quiz**: Generate ${q.mcq || 10} Multiple Choice Questions, ${q.ar || 5} Assertion-Reasoning questions, and ${q.detailed || 3} Detailed Answer questions with answer key.\n`;
        }
        if (settings.outputs.handout) {
            prompt += `- **Visual Handout**: Create a one-page visual summary with diagrams, charts, or flowcharts.\n`;
        }
        prompt += `\n`;
    }

    // Add grade/subject context if available
    if (settings.grade) {
        prompt += `**Grade Level:** ${settings.grade}\n`;
    }
    if (settings.subject) {
        prompt += `**Subject:** ${settings.subject}\n`;
    }

    return prompt.trim();
}

/**
 * Extract subject name from filename
 */
function extractSubjectFromFilename(filename) {
    const lower = filename.toLowerCase();
    const subjects = {
        'biology': 'Biology',
        'chemistry': 'Chemistry',
        'physics': 'Physics',
        'math': 'Mathematics',
        'english': 'English',
        'grammar': 'Grammar',
        'history': 'History',
        'geography': 'Geography'
    };

    for (const [key, value] of Object.entries(subjects)) {
        if (lower.includes(key)) return value;
    }
    return null;
}

/**
 * Generate combined report prompt with all options
 * @param {Array} selectedPrompts - Array of selected prompt objects
 * @param {Object} studyGuideOptions - Study guide checkbox states
 * @param {Object} handoutOptions - Handout checkbox states
 * @param {string} manualStudyGuide - Custom study guide text
 * @param {string} manualHandout - Custom handout text
 * @returns {string} - Combined report prompt for NotebookLM
 */
export function generateReportPrompt(
    selectedPrompts = [],
    studyGuideOptions = {},
    handoutOptions = {},
    manualStudyGuide = '',
    manualHandout = '',
    dashboardSettings = {}
) {
    let report = `# NotebookLM Combined Report Prompt\n\n`;

    if (selectedPrompts && selectedPrompts.length > 0) {
        report += `Generated from ${selectedPrompts.length} selected template(s)\n\n`;

        // List selected files
        report += `## Source Files\n`;
        selectedPrompts.forEach((p, idx) => {
            report += `${idx + 1}. ${p.filename} (${p.source})\n`;
        });
        report += `\n`;
    } else if (dashboardSettings && dashboardSettings.topic) {
        report += `Generated for Topic: ${dashboardSettings.topic}\n`;
        if (dashboardSettings.grade) report += `Grade: ${dashboardSettings.grade}\n`;
        if (dashboardSettings.subject) report += `Subject: ${dashboardSettings.subject}\n`;
        report += `\n`;
    } else {
        // Fallback for empty state
        if (!manualStudyGuide && !manualHandout && Object.keys(studyGuideOptions).length === 0) {
            return '';
        }
    }

    // Add study guide options
    const activeStudyOptions = Object.entries(studyGuideOptions)
        .filter(([key, val]) => val)
        .map(([key]) => key);

    if (activeStudyOptions.length > 0 || manualStudyGuide) {
        report += `## Study Guide Requirements\n`;
        report += `Please create a study guide including:\n\n`;

        if (activeStudyOptions.includes('assertion')) {
            report += `- **Assertions**: Key statements and claims from the material\n`;
        }
        if (activeStudyOptions.includes('concept')) {
            report += `- **Core Concepts**: Main ideas and definitions\n`;
        }
        if (activeStudyOptions.includes('clarification')) {
            report += `- **Clarifications**: Detailed explanations of complex topics\n`;
        }
        if (activeStudyOptions.includes('examples')) {
            report += `- **Examples**: Illustrative examples and case studies\n`;
        }
        if (activeStudyOptions.includes('summary')) {
            report += `- **Summary**: Concise overview of all topics\n`;
        }
        if (activeStudyOptions.includes('key-terms')) {
            report += `- **Key Terms**: Important vocabulary and terminology\n`;
        }

        if (manualStudyGuide) {
            report += `\n**Additional Instructions**: ${manualStudyGuide}\n`;
        }
        report += `\n`;
    }

    // Add handout options
    const activeHandoutOptions = Object.entries(handoutOptions)
        .filter(([key, val]) => val)
        .map(([key]) => key);

    if (activeHandoutOptions.length > 0 || manualHandout) {
        report += `## Visual Handout Requirements\n`;
        report += `Please create visual representations including:\n\n`;

        if (activeHandoutOptions.includes('timeline')) {
            report += `- **Timeline**: Chronological view of events or processes\n`;
        }
        if (activeHandoutOptions.includes('flowchart')) {
            report += `- **Flowchart**: Step-by-step process diagram\n`;
        }
        if (activeHandoutOptions.includes('decision-tree')) {
            report += `- **Decision Tree**: Decision-making branching diagram\n`;
        }
        if (activeHandoutOptions.includes('mind-map')) {
            report += `- **Mind Map**: Visual connections between concepts\n`;
        }
        if (activeHandoutOptions.includes('table')) {
            report += `- **Comparison Table**: Structured data comparison\n`;
        }
        if (activeHandoutOptions.includes('equation-helper')) {
            report += `- **Equation Helper**: Mathematical formulas and explanations\n`;
        }
        if (activeHandoutOptions.includes('tips')) {
            report += `- **Tips & Tricks**: Quick reference guide\n`;
        }
        if (activeHandoutOptions.includes('comparison')) {
            report += `- **Comparison Chart**: Pro/con or comparative analysis\n`;
        }
        if (activeHandoutOptions.includes('checklist')) {
            report += `- **Checklist**: Action items and key points\n`;
        }

        if (manualHandout) {
            report += `\n**Additional Instructions**: ${manualHandout}\n`;
        }
        report += `\n`;
    }

    // Add individual prompts
    if (selectedPrompts && selectedPrompts.length > 0) {
        report += `## Detailed Source Prompts\n\n`;
        report += `---\n\n`;
        selectedPrompts.forEach((p, idx) => {
            report += `### Source ${idx + 1}: ${p.filename}\n\n`;
            report += p.prompt;
            report += `\n\n---\n\n`;
        });
    }

    // Footer instructions
    report += `## Generation Instructions (IMPORTANT)\n`;
    report += `Please synthesize all the above sources and generate the following distinct sections in a single response:\n\n`;

    if (studyGuideOptions['csv-format']) {
        report += `### SECTION 1: DATA EXPORT (CSV FORMAT)\n`;
        report += `- Provide a raw CSV code block containing the synthesized data.\n`;
        report += `- Follow all column headers specified in the Source Prompts above.\n`;
        report += `- Ensure the CSV is Excel-compatible (use commas, escape with quotes).\n\n`;
    }

    report += `### SECTION 2: STUDY MATERIAL (WORD/MARKDOWN FORMAT)\n`;
    report += `- Provide a comprehensive study guide and visual handout descriptions in structured Markdown.\n`;
    report += `- This section should be optimized for copy-pasting into a Word document.\n`;
    report += `- Use clear headings, bullet points, and bold text for readability.\n\n`;

    report += `### SECTION 3: QUIZ & ASSESSMENT\n`;
    report += `- If a quiz was requested, provide it here with a clear Answer Key at the end.\n\n`;

    report += `GENERAL RULES:\n`;
    report += `1. Maintain high educational quality and age-appropriateness.\n`;
    report += `2. Do not combine the CSV and the Study Material into the same block.\n`;
    report += `3. Use clear separators between sections.\n`;

    return report;
}
