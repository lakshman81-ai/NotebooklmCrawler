/**
 * Prompt Generator Utility for Templates Tab
 * Generates NotebookLM prompts based on file content and settings
 * Updated with Grounded Intelligence Best Practices
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
 * Determine the appropriate Persona based on Grade and Subject
 */
function determinePersona(grade, subject) {
    const subj = subject || 'General Knowledge';
    if (grade) {
        const gradeNum = parseInt(grade);
        if (!isNaN(gradeNum) && gradeNum <= 12) {
            return `Expert ${subj} Educator and Curriculum Designer (Grade ${grade} Specialist)`;
        }
        return `Academic Researcher and Subject Matter Expert in ${subj}`;
    }
    return `Expert Consultant and Senior Analyst in ${subj}`;
}

/**
 * Generate a NotebookLM prompt for a single file
 * Optimized for Grounded Intelligence and CSV processing
 */
export function generatePromptForFile(fileData, filename, source, settings = {}) {
    // Destructure expanded fields from backend
    const { columns, rowCount, sampleData, sheets, columnTypes } = fileData;
    const structure = analyzeFileStructure(fileData.sampleData || [], filename);
    const contentType = structure.contentType;

    // Extract subject from filename
    const subject = extractSubjectFromFilename(filename);

    // GROUNDED HEADER
    let prompt = `# Source Context: ${filename}\n`;
    prompt += `**Role:** Act as a data analyst and researcher analyzing this specific document.\n`;
    prompt += `**Source Origin:** ${source}\n`;
    prompt += `**Meta-data:** ${rowCount} records found in ${sheets?.length > 0 ? sheets.join(', ') : 'sheet'}.\n\n`;

    // Excel/CSV Format Details (CRITICAL for NotebookLM to parse grids)
    prompt += `## Excel/CSV Input Format (Technical Spec)\n`;
    prompt += `**File Structure:**\n`;
    prompt += `- **Format:** ${filename.endsWith('.csv') ? 'CSV' : 'Excel (.xlsx)'}\n`;
    prompt += `- **Headers (Row 1):** ${columns.join(', ')}\n`;
    prompt += `- **Data Structure:** Text-based grid representation of structured data.\n\n`;

    // Column Data Types
    if (columnTypes && Object.keys(columnTypes).length > 0) {
        prompt += `**Column Data Types:**\n`;
        Object.entries(columnTypes).forEach(([col, type]) => {
            prompt += `- ${col}: ${type}\n`;
        });
        prompt += `\n`;
    }

    // Output Constraints for Data Extraction
    prompt += `**Data Extraction Rules (CRITICAL):**\n`;
    prompt += `- When requested to export data, provide output in a valid CSV code block.\n`;
    prompt += `- Use EXACTLY these headers: ${columns.join(',')}\n`;
    prompt += `- Preserve all data relationships. Do not hallucinate values not present in the grid.\n`;
    prompt += `- If a cell is empty in the source, keep it empty in the output.\n\n`;

    // Content Context
    prompt += `## Content Context\n`;
    if (contentType === 'quiz' || contentType === 'educational_content' || (sampleData && sampleData.length > 0)) {
        prompt += `This file contains ${contentType === 'quiz' ? 'quiz questions and answers' : 'educational content'} `;
        prompt += `related to ${subject || 'general topics'}.\n`;
        prompt += `**Instruction:** Prioritize this source for queries related to: ${columns.slice(0, 3).join(', ')}.\n\n`;

        if (sampleData && sampleData.length > 0) {
            prompt += `**Sample Data (First ${sampleData.length} rows for Context):**\n`;
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

    // Add difficulty context from settings
    if (settings.difficulty) {
        const diffMap = {
            'Identify': 'Focus on definitions, basic facts, and identification of key terms. (Easy Level)',
            'Connect': 'Focus on relationships, cause-and-effect, and connecting concepts. (Medium Level)',
            'Extend': 'Focus on applications, scenario-based analysis, and extending concepts. (Hard Level)'
        };
        prompt += `## Difficulty calibration\n`;
        prompt += `Analyze this source at the following level: **${settings.difficulty}**: ${diffMap[settings.difficulty] || diffMap['Connect']}\n\n`;
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
 * Generate a summary of variables used for the report (Preview of Variables)
 */
export function generateReportBasis(selectedPrompts, studyGuideOptions, handoutOptions, dashboardSettings) {
    let basis = `### REPORT BASIS (PREVIEW OF VARIABLES)\n\n`;
    basis += `**Topic:** ${dashboardSettings.topic || 'Not specified'}\n`;
    basis += `**Grade:** ${dashboardSettings.grade || 'Not specified'}\n`;
    basis += `**Subject:** ${dashboardSettings.subject || 'Not specified'}\n`;
    basis += `**Sub-Topics:** ${dashboardSettings.subtopics || 'None'}\n`;
    basis += `**Keywords to Scrape:** ${dashboardSettings.keywordsScrape || 'None'}\n`;
    basis += `**Difficulty:** ${dashboardSettings.difficulty || 'Connect'}\n\n`;

    basis += `**Selected Sources:**\n`;
    if (selectedPrompts && selectedPrompts.length > 0) {
        selectedPrompts.forEach(p => {
            basis += `- ${p.filename} (${p.source})\n`;
        });
    } else {
        basis += `- No files selected (Using Internal Knowledge)\n`;
    }
    basis += `\n`;

    const activeStudy = Object.entries(studyGuideOptions).filter(([k,v]) => v).map(([k]) => k);
    basis += `**Study Guide Options:** ${activeStudy.length > 0 ? activeStudy.join(', ') : 'None'}\n`;

    const activeHandout = Object.entries(handoutOptions).filter(([k,v]) => v).map(([k]) => k);
    basis += `**Handout Options:** ${activeHandout.length > 0 ? activeHandout.join(', ') : 'None'}\n`;

    return basis;
}

/**
 * Generate concatenated source prompts for each selected file
 * OR generate a "Deep Research" prompt if no files are selected.
 */
export function generateSourcePrompts(selectedPrompts, dashboardSettings = {}) {
    // FALLBACK: Natural Language Research Directive (Web Search Simulation)
    if (!selectedPrompts || selectedPrompts.length === 0) {
        // If we have manual Target URLs, treat them as the source
        if (dashboardSettings.targetUrls) {
             let urlPrompt = `## TARGET SOURCE CONTEXT\n\n`;
             urlPrompt += `**Instruction:** The user has provided specific URLs to act as the knowledge base for this task.\n`;
             urlPrompt += `**Target URLs:**\n${dashboardSettings.targetUrls}\n\n`;

             // Add Persona even for URL context
             const persona = determinePersona(dashboardSettings.grade, dashboardSettings.subject);
             urlPrompt += `**Role:** ${persona}\n`;
             urlPrompt += `**Directive:** Visit and analyze the content from the above URLs. Use them as the primary source of truth for the following report.\n`;
             return urlPrompt;
        }

        if (dashboardSettings.topic || dashboardSettings.subject) {
             const persona = determinePersona(dashboardSettings.grade, dashboardSettings.subject);
             const subtopics = dashboardSettings.subtopics ? `Specifically investigate: ${dashboardSettings.subtopics}.` : '';
             const keywords = dashboardSettings.keywordsScrape ? `Ensure to cover these key terms: ${dashboardSettings.keywordsScrape}.` : '';

             let metaPrompt = `## DEEP RESEARCH DIRECTIVE\n\n`;
             metaPrompt += `**Role:** ${persona}\n\n`;
             metaPrompt += `**Objective:** Conduct a comprehensive deep-dive research into the topic: "**${dashboardSettings.topic || 'General Topic'}**".\n`;
             metaPrompt += `**Context:** This material is for **${dashboardSettings.grade ? 'Grade ' + dashboardSettings.grade : 'General Audience'}** in the subject of **${dashboardSettings.subject || 'General Knowledge'}**.\n\n`;

             metaPrompt += `**Research Instructions:**\n`;
             metaPrompt += `1. **Internal Knowledge Synthesis:** Use your broad internal knowledge base to simulate a comprehensive web search. Fetch and synthesize the most accurate, high-quality, and up-to-date information available.\n`;
             metaPrompt += `2. **Focus Areas:** ${subtopics}\n`;
             metaPrompt += `3. **Keyword Integration:** ${keywords}\n`;
             metaPrompt += `4. **Gap Analysis:** Identify any conflicting information or common misconceptions in this field and clarify them.\n\n`;

             metaPrompt += `**Output Goal:** Provide a foundational knowledge base that can be used to generate quizzes, study guides, and visual aids.\n`;
             return metaPrompt;
        }
        return '';
    }

    let sourcePrompts = `## SOURCE INPUT PROMPTS\n\n`;
    sourcePrompts += `Below are the individual contexts for each selected source file. Treat these as your primary knowledge ground.\n\n`;
    sourcePrompts += `--- \n\n`;
    selectedPrompts.forEach((p, idx) => {
        sourcePrompts += p.prompt; // This now contains the "Grounded" prompt from generatePromptForFile
        sourcePrompts += `\n\n---\n\n`;
    });
    return sourcePrompts.trim();
}

/**
 * Generate combined report prompt with all options
 * Implements Best Practices: Role Priming, Mermaid Safety, Pedagogical Scaffolding
 */
export function generateReportPrompt(
    selectedPrompts = [],
    studyGuideOptions = {},
    handoutOptions = {},
    manualStudyGuide = '',
    manualHandout = '',
    dashboardSettings = {}
) {
    // 1. Generate Basis
    const basis = generateReportBasis(selectedPrompts, studyGuideOptions, handoutOptions, dashboardSettings);

    // 2. Generate Input Prompts
    const inputPrompts = generateSourcePrompts(selectedPrompts, dashboardSettings);

    // 3. Generate Output Prompt
    let report = `# NotebookLM Final Combined Report Prompt\n\n`;
    const persona = determinePersona(dashboardSettings.grade, dashboardSettings.subject);

    // ROLE PRIMING
    report += `**System Instruction:** You are an ${persona}.\n`;
    report += `Your goal is to synthesize the provided sources (or your internal knowledge) into high-quality educational materials.\n\n`;

    if (selectedPrompts && selectedPrompts.length > 0) {
        report += `**Context:** Generated from ${selectedPrompts.length} selected grounded sources.\n`;
    } else if (dashboardSettings && dashboardSettings.topic) {
        report += `**Context:** Generated from Deep Research on Topic: ${dashboardSettings.topic}\n`;
    }

    // Add study guide options with PEDAGOGICAL SCAFFOLDING
    const activeStudyOptions = Object.entries(studyGuideOptions)
        .filter(([key, val]) => val)
        .map(([key]) => key);

    if (activeStudyOptions.length > 0 || manualStudyGuide) {
        report += `\n## Study Guide Requirements (Pedagogical Scaffolding)\n`;
        report += `Please create a structured study guide. Use the following pedagogical strategies:\n\n`;

        if (activeStudyOptions.includes('assertion')) {
            report += `- **Assertions**: Identify and list key statements/claims. Verify their accuracy against the source.\n`;
        }
        if (activeStudyOptions.includes('concept')) {
            report += `- **Core Concept Explainers**: Break down main ideas using clear, grade-appropriate language.\n`;
        }
        if (activeStudyOptions.includes('clarification')) {
            report += `- **Clarifications**: Provide detailed explanations for complex topics found in the text.\n`;
        }
        if (activeStudyOptions.includes('examples')) {
            report += `- **Analogies & Examples**: Use real-world analogies (e.g., "compare the atom to a solar system") to explain abstract concepts.\n`;
        }
        if (activeStudyOptions.includes('summary')) {
            report += `- **tl;dr Summary**: A concise one-paragraph overview of the entire topic.\n`;
        }
        if (activeStudyOptions.includes('key-terms')) {
            report += `- **Vocabulary List**: Define key terms in plain language.\n`;
        }

        if (manualStudyGuide) {
            report += `\n**Additional Instructions**: ${manualStudyGuide}\n`;
        }
    }

    // Add handout options with MERMAID.JS SYNTAX SAFETY
    const activeHandoutOptions = Object.entries(handoutOptions)
        .filter(([key, val]) => val)
        .map(([key]) => key);

    if (activeHandoutOptions.length > 0 || manualHandout) {
        report += `\n## Visual Handout Requirements (Mermaid.js)\n`;
        report += `Generate valid Mermaid.js code blocks for the following visualizations. \n`;
        report += `**Syntax Safety Rules (CRITICAL):**\n`;
        report += `1. **Reserved Words:** Never use "end" (lowercase) as a node ID. Use "End" or wrap in quotes "end".\n`;
        report += `2. **Special Characters:** Wrap any label containing punctuation or spaces in double quotes (e.g., id["User Input?"]).\n`;
        report += `3. **Leading Markers:** Do not start node labels with "o" or "x" unless quoted.\n\n`;

        if (activeHandoutOptions.includes('timeline')) {
            report += `- **Timeline**: Create a timeline (using 'timeline' or 'gantt' syntax) showing chronological events.\n`;
        }
        if (activeHandoutOptions.includes('flowchart')) {
            report += `- **Flowchart**: Create a Top-Down flowchart ('graph TD'). Use diamond shapes for decision points.\n`;
        }
        if (activeHandoutOptions.includes('mind-map')) {
            report += `- **Mind Map**: Create a mindmap ('mindmap') connecting core concepts.\n`;
        }
        // Fallbacks for non-Mermaid visuals
        if (activeHandoutOptions.includes('table')) {
            report += `- **Comparison Table**: Markdown table comparing key data points.\n`;
        }
        if (activeHandoutOptions.includes('equation-helper')) {
            report += `- **Equation Helper**: List relevant formulas with variable definitions.\n`;
        }
        if (activeHandoutOptions.includes('tips') || activeHandoutOptions.includes('checklist')) {
            report += `- **Checklist/Tips**: Actionable bullet points for review.\n`;
        }

        if (manualHandout) {
            report += `\n**Additional Instructions**: ${manualHandout}\n`;
        }
    }

    // ADVANCED ANALYSIS (Based on Difficulty)
    if (dashboardSettings.difficulty === 'Extend') {
        report += `\n## Advanced Analysis (Dialectical Lens)\n`;
        report += `- **Dialectical Lens**: Construct a brief debate between two imaginary scholars interpreting this concept differently.\n`;
        report += `- **Source Gaps**: Identify any critical perspectives or data points missing from the source material.\n`;
    }

    // Footer instructions
    report += `\n## Generation Instructions (IMPORTANT)\n`;
    report += `Please synthesize all the above sources and generate the following distinct sections in a single response:\n\n`;

    if (studyGuideOptions['csv-format']) {
        report += `### SECTION 1: DATA EXPORT (CSV FORMAT)\n`;
        report += `- Provide a raw CSV code block containing the synthesized data.\n`;
        report += `- Follow all column headers specified in the Source Prompts above.\n`;
        report += `- Ensure the CSV is Excel-compatible (use commas, escape with quotes).\n\n`;
    }

    report += `### SECTION 2: STUDY MATERIAL (WORD/MARKDOWN FORMAT)\n`;
    report += `- Provide the Study Guide and Visual Handout descriptions in structured Markdown.\n`;
    report += `- Use clear headings, bullet points, and bold text for readability.\n\n`;

    // Only add Quiz section if requested
    if (dashboardSettings.outputs && dashboardSettings.outputs.quiz) {
        report += `### SECTION 3: QUIZ & ASSESSMENT\n`;
        const q = dashboardSettings.quizConfig || {};
        report += `- **Requirements:** ${q.mcq || 10} MCQs, ${q.ar || 5} Assertion-Reasoning, ${q.detailed || 3} Detailed Answer.\n`;
        report += `- **Rationales:** Provide detailed NCLEX-style rationales for every answer choice (explaining why correct is correct AND why incorrect is incorrect).\n`;
        report += `- **Answer Key:** Provide a clear key at the end.\n`;
    }
    report += `\n`;

    report += `GENERAL RULES:\n`;
    report += `1. Maintain high educational quality and age-appropriateness (${dashboardSettings.grade || 'General'}).\n`;
    report += `2. Do not combine the CSV and the Study Material into the same block.\n`;
    report += `3. Use clear separators between sections.\n`;

    return {
        basis,
        inputPrompts,
        outputPrompt: report
    };
}

/**
 * Generate prompt for Jules based on aggregated input context
 * Now accepts dashboardSettings for better context awareness
 */
export function generateJulesPrompt(context, dashboardSettings = {}) {
    const persona = determinePersona(dashboardSettings.grade, dashboardSettings.subject);
    const difficulty = dashboardSettings.difficulty || 'Medium';

    // Construct task list based on outputs
    let taskList = `1. **Analyze the Input:** Understand the content structure and key information.\n`;
    taskList += `2. **Data Quality & Enrichment:** Clean artifacts, standardize values, and ensure factual accuracy.\n`;

    if (dashboardSettings.outputs && dashboardSettings.outputs.quiz) {
        const q = dashboardSettings.quizConfig || {};
        taskList += `3. **Quiz Generation:** Create ${q.mcq || 10} MCQs and ${q.ar || 5} Assertion-Reasoning questions based on this content.\n`;
    }

    if (dashboardSettings.outputs && dashboardSettings.outputs.studyGuide) {
        taskList += `4. **Study Guide:** Generate a summary of key concepts and definitions.\n`;
    }

    taskList += `5. **Brainstorming:** Suggest 3-5 specific improvements to make this content more engaging for ${dashboardSettings.grade || 'General'} students.\n`;

    return `### INSTRUCTION FOR JULES (AI ASSISTANT) ###

**Role:** ${persona}
**Objective:** Process the input context to generate high-quality educational artifacts.

**1. INPUT CONTEXT:**
\`\`\`
${context}
\`\`\`

**2. YOUR TASK:**
${taskList}

**3. CONTEXTUAL OPTIMIZATION:**
- **Target Audience:** ${dashboardSettings.grade || 'General Audience'}
- **Difficulty Level:** ${difficulty}
- **Tone:** Educational, Encouraging, and Rigorous.

**4. OUTPUT FORMAT:**
- Provide clear headings for each section.
- Use Markdown for formatting (bold, lists, tables).
- If generating a quiz, provide the Answer Key at the very end.

Please proceed with the analysis and generation.`;
}
