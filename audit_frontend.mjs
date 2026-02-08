
/**
 * Prompt Generator Utility for Templates Tab
 * Generates NotebookLM prompts based on file content and settings
 * Updated with Grounded Intelligence Best Practices
 */

import { generatePromptForFile, generateReportPrompt, generateJulesPrompt, generateSourcePrompts } from './frontend/src/components/Templates/promptGenerator.js';

// TEST HARNESS
async function main() {
    console.log("=== AUDITING PROMPTS ===\n");

    // TEST CASE 1: NotebookLM Prompt with CSV File
    console.log("--- TEST CASE 1: NotebookLM Prompt (CSV File) ---");
    const fileData = {
        columns: ["ID", "Question", "Answer", "Difficulty"],
        rowCount: 10,
        sampleData: [{ID: 1, Question: "What is 2+2?", Answer: "4", Difficulty: "Easy"}],
        sheets: ["Sheet1"],
        columnTypes: {ID: "int", Question: "string", Answer: "string", Difficulty: "string"}
    };
    const settings = {
        difficulty: "Connect",
        grade: "8",
        subject: "Math",
        topic: "Arithmetic",
        keywordsScrape: "addition, subtraction",
        outputs: { quiz: true, studyGuide: true }
    };

    const filePrompt = generatePromptForFile(fileData, "math_quiz.csv", "Internal Upload", settings);
    console.log(filePrompt);
    console.log("\n------------------------------------------------\n");

    // TEST CASE 2: NotebookLM Report Prompt (Combined)
    console.log("--- TEST CASE 2: NotebookLM Report Prompt (Combined) ---");
    const selectedPrompts = [{filename: "math_quiz.csv", source: "Internal Upload", prompt: filePrompt}];
    const studyGuideOptions = {"concept": true, "examples": true, "csv-format": true};
    const handoutOptions = {"flowchart": true};
    const reportPrompt = generateReportPrompt(selectedPrompts, studyGuideOptions, handoutOptions, "", "", settings);
    console.log(reportPrompt.outputPrompt);
    console.log("\n------------------------------------------------\n");

    // TEST CASE 3: Jules Prompt
    console.log("--- TEST CASE 3: Jules Prompt ---");
    // Passing settings now!
    const julesPrompt = generateJulesPrompt("Input context from a file or search result...", settings);
    console.log(julesPrompt);
    console.log("\n------------------------------------------------\n");

    // TEST CASE 4: NotebookLM URL-based Prompt
    console.log("--- TEST CASE 4: NotebookLM URL-based Prompt ---");
    const urlSettings = {
        targetUrls: "https://example.com/article1, https://example.com/article2",
        grade: "10",
        subject: "Biology",
        topic: "Cell Structure"
    };
    const urlPrompt = generateSourcePrompts([], urlSettings);
    console.log(urlPrompt);
    console.log("\n------------------------------------------------\n");
}

main();
