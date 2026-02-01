# Testing Instructions for NotebookLM Modular System

**Target Audience**: AI Agents (Claude, Antigravity, etc.) and Developers
**Prerequisites**: Python 3.8+, Windows/Linux/macOS
**Execution Mode**: Sequential command execution

---

## Setup Phase (One-Time)

### Step 1: Navigate to Project Directory
```bash
cd C:\Code\NotebooklmCrawler
```

**Expected Output**: Current working directory is `C:\Code\NotebooklmCrawler`
**Verification**: Run `pwd` (Linux/macOS) or `cd` (Windows) to confirm

---

### Step 2: Install Required Dependencies

#### Core Dependencies (Required)
```bash
pip install pydantic playwright beautifulsoup4
```

**Expected Output**: `Successfully installed pydantic-X.X.X playwright-X.X.X beautifulsoup4-X.X.X`

#### Optional Dependencies for Format Conversion

**For Excel Support**:
```bash
pip install openpyxl
```

**For PDF Support (Option A - pdfkit)**:
```bash
pip install pdfkit
```
Then install wkhtmltopdf:
- **Windows**: Download from https://wkhtmltopdf.org/downloads.html
- **Linux**: `sudo apt-get install wkhtmltopdf`
- **macOS**: `brew install wkhtmltopdf`

**For PDF Support (Option B - weasyprint)**:
```bash
pip install weasyprint
```

**For DOCX Support**:
```bash
pip install pypandoc
```
Then install pandoc:
- **Windows**: Download from https://pandoc.org/installing.html
- **Linux**: `sudo apt-get install pandoc`
- **macOS**: `brew install pandoc`

**For Markdown Rendering**:
```bash
pip install markdown
```

**Verification**:
```bash
python -c "import openpyxl, markdown; print('✓ Basic conversion dependencies installed')"
```

---

## Test Execution Modes

### MODE 1: Basic Prompt Generation Test (No Browser Required)

**Purpose**: Verify all prompt generation modules work correctly
**Duration**: ~10 seconds
**Browser Required**: NO
**Network Required**: NO

**Command**:
```bash
python examples/test_modular_system.py
```

**Expected Output**:
```
==================================================
TEST 1: Prompt Generation Modules
==================================================
Content Request: Grade 8 Physics Gravity

--- Module A: Input Source Prompt Generation ---
Primary Search Query: CK-12 physical science gravity grade 8 mass weight Newton open educational resources...
Conceptual Search: Grade 8 physics gravity conceptual explanation mass vs weight distinction...
Source Weighting: {'toggle_on': ['CK-12', 'Khan Academy'], 'toggle_off': [...]}

--- Module B/C/D: Output Prompt Generation ---
Quiz Prompt Length: 1234 chars
Quiz Prompt Preview:
Act as a Grade 8 Physics assessment specialist...

Study Guide Prompt Length: 2345 chars
Study Guide Preview:
Generate a comprehensive 'Grade 8 Gravity Study Guide'...

Handout Prompt Length: 1567 chars

--- Prompt Validation ---
Quiz Prompt Valid: True

✓ TEST 1 COMPLETE: All prompt modules working correctly

==================================================
TEST 2: Format Conversion
==================================================

--- Converting CSV to Excel ---
✓ Excel file created: outputs/test/test_quiz.xlsx

--- Converting Markdown to HTML ---
✓ HTML file created: outputs/test/test_study_guide.html

--- Converting Markdown to PDF ---
✓ PDF file created: outputs/test/test_study_guide.pdf

--- Batch Conversion Test ---
✓ Batch conversion complete: 3 files created
  - excel: outputs/test/grade8_gravity_quiz.xlsx
  - html: outputs/test/grade8_gravity_study_guide.html
  - pdf: outputs/test/grade8_gravity_study_guide.pdf

✓ TEST 2 COMPLETE: Format conversion working

==================================================
TEST 3: Full Workflow Simulation
==================================================
Mode: UNGUIDED

--- PHASE 1: Direct Upload (UNGUIDED) ---
(In real workflow: Upload chunks via file picker)

--- PHASE 2: Output Prompt Generation ---
Generated 3 prompts: quiz (1234 chars), guide (2345 chars), handout (1567 chars)

--- PHASE 3: Mock NotebookLM Output ---
Mock results: ['quiz_csv', 'study_guide_md', 'visuals_md']

--- PHASE 4: Format Conversion ---
✓ Converted to 3 formats:
  - excel: outputs/test_workflow/grade8_gravity_quiz.xlsx
  - html: outputs/test_workflow/grade8_gravity_study_guide.html
  - pdf: outputs/test_workflow/grade8_gravity_handout.html

✓ TEST 3 COMPLETE: Full workflow simulation successful

==================================================
ALL TESTS PASSED ✓
==================================================
```

**Success Criteria**:
- ✅ All 3 tests complete without errors
- ✅ Output files created in `outputs/test/` directory
- ✅ Console shows "ALL TESTS PASSED ✓"

**Failure Handling**:
- If `openpyxl` missing: Excel test skipped with warning
- If `pdfkit`/`weasyprint` missing: PDF test skipped with warning
- If any prompt validation fails: Check error messages in output

---

### MODE 2: Test with GUIDED Mode Environment

**Purpose**: Simulate guided mode workflow (NotebookLM discovers sources)
**Duration**: ~15 seconds
**Browser Required**: NO (simulation only)
**Network Required**: NO

**Command (Windows)**:
```bash
set NOTEBOOKLM_GUIDED=true
python examples/test_modular_system.py --mode guided
```

**Command (Linux/macOS)**:
```bash
export NOTEBOOKLM_GUIDED=true
python examples/test_modular_system.py --mode guided
```

**Expected Output Difference**:
```
TEST 3: Full Workflow Simulation
Mode: GUIDED

--- PHASE 1: Input Source Prompt Generation (GUIDED) ---
Would inject search query: CK-12 physical science gravity grade 8 mass weight...
(In real workflow: InputSourcePromptInjector.inject_source_discovery_prompts())
```

**Success Criteria**:
- ✅ Console shows "Mode: GUIDED"
- ✅ PHASE 1 shows "Input Source Prompt Generation (GUIDED)"
- ✅ Search query is displayed (not upload message)

---

### MODE 3: Test with UNGUIDED Mode Environment

**Purpose**: Simulate unguided mode workflow (Direct upload)
**Duration**: ~15 seconds
**Browser Required**: NO (simulation only)
**Network Required**: NO

**Command (Windows)**:
```bash
set NOTEBOOKLM_GUIDED=false
python examples/test_modular_system.py --mode unguided
```

**Command (Linux/macOS)**:
```bash
export NOTEBOOKLM_GUIDED=false
python examples/test_modular_system.py --mode unguided
```

**Expected Output Difference**:
```
Mode: UNGUIDED

--- PHASE 1: Direct Upload (UNGUIDED) ---
(In real workflow: Upload chunks via file picker)
```

**Success Criteria**:
- ✅ Console shows "Mode: UNGUIDED"
- ✅ PHASE 1 shows "Direct Upload (UNGUIDED)"
- ✅ No search query generation

---

### MODE 4: View Usage Examples

**Purpose**: Display usage examples for all configurations
**Duration**: Instant

**Command**:
```bash
python examples/test_modular_system.py --examples
```

**Expected Output**:
```
==================================================
USAGE EXAMPLES
==================================================

# Example 1: Guided Mode (NotebookLM discovers sources)
export NOTEBOOKLM_GUIDED=true
export CR_GRADE="Grade 8"
export CR_TOPIC="Physics Gravity"
export CR_DIFFICULTY="Medium"
export CR_OUTPUT_CONFIG='{"studyGuide":true,"quiz":true,"handout":true}'
export CR_QUIZ_CONFIG='{"mcq":10,"ar":5,"detailed":3}'
python run.py

# Example 2: Unguided Mode (Upload pre-crawled content)
export NOTEBOOKLM_GUIDED=false
export TARGET_URL="https://byjus.com/jee/gravitation/"
export CR_GRADE="Grade 8"
export CR_TOPIC="Gravitation"
python run.py

# Example 3: Multi-Report Generation
export CR_MULTI_REPORT_TYPES="student,teacher,admin"
export CR_OUTPUT_FORMATS="excel,pdf,html"
python run.py

# Example 4: Test Prompt Generation Only
python examples/test_modular_system.py
```

---

## Full Integration Test with Browser (Advanced)

### Prerequisites
1. Install Playwright browsers:
```bash
playwright install chromium
```

2. Configure `.env` file in project root:
```env
# Mode Selection
NOTEBOOKLM_GUIDED=true

# Content Request Parameters
CR_GRADE=Grade 8
CR_TOPIC=Physics Gravity
CR_DIFFICULTY=Medium
CR_OUTPUT_CONFIG={"studyGuide":true,"quiz":true,"handout":true}
CR_QUIZ_CONFIG={"mcq":10,"ar":5,"detailed":3}
CR_OUTPUT_FORMATS=excel,pdf,html
CR_MULTI_REPORT_TYPES=student,teacher

# Optional: Direct URL for guided mode
TARGET_URL=

# Optional: Local file path for unguided mode
LOCAL_FILE_PATH=
```

### Test Case 1: GUIDED Mode with Browser Automation

**Command (Windows)**:
```bash
set NOTEBOOKLM_GUIDED=true
set CR_GRADE=Grade 8
set CR_TOPIC=Physics Gravity
set CR_DIFFICULTY=Medium
set CR_OUTPUT_CONFIG={"studyGuide":true,"quiz":true}
set CR_QUIZ_CONFIG={"mcq":10,"ar":5}
python run.py
```

**Command (Linux/macOS)**:
```bash
export NOTEBOOKLM_GUIDED=true
export CR_GRADE="Grade 8"
export CR_TOPIC="Physics Gravity"
export CR_DIFFICULTY="Medium"
export CR_OUTPUT_CONFIG='{"studyGuide":true,"quiz":true}'
export CR_QUIZ_CONFIG='{"mcq":10,"ar":5}'
python run.py
```

**Expected Workflow**:
1. Browser opens to notebooklm.google.com
2. System waits for Google login (manual)
3. After login: Navigates to "New notebook"
4. Clicks "Add source" → "Search the web"
5. Injects search query: "CK-12 physical science gravity grade 8..."
6. Imports search results
7. Navigates to "Notebook guide" → "Create Your Own"
8. Injects quiz prompt → Extracts CSV
9. Injects study guide prompt → Extracts Markdown
10. Converts outputs to Excel and PDF
11. Saves to `outputs/final/`

**Success Criteria**:
- ✅ Browser automation completes without crashes
- ✅ Files created: `grade8_physics_gravity_quiz.xlsx`, `grade8_physics_gravity_study_guide.pdf`
- ✅ Console shows "✓ NotebookLM modular generation complete"

---

### Test Case 2: UNGUIDED Mode with Browser Automation

**Command (Windows)**:
```bash
set NOTEBOOKLM_GUIDED=false
set TARGET_URL=https://byjus.com/jee/gravitation/
set CR_GRADE=Grade 8
set CR_TOPIC=Gravitation
python run.py
```

**Command (Linux/macOS)**:
```bash
export NOTEBOOKLM_GUIDED=false
export TARGET_URL="https://byjus.com/jee/gravitation/"
export CR_GRADE="Grade 8"
export CR_TOPIC="Gravitation"
python run.py
```

**Expected Workflow**:
1. Crawler fetches content from TARGET_URL
2. Chunks content into sections
3. Browser opens to notebooklm.google.com
4. System waits for Google login (manual)
5. After login: Navigates to "New notebook"
6. Clicks "Upload" → Uploads generated PDF/HTML
7. Waits for source processing
8. Navigates to "Notebook guide" → "Create Your Own"
9. Injects quiz/study guide prompts
10. Extracts and converts outputs

**Success Criteria**:
- ✅ URL crawling completes
- ✅ File upload succeeds
- ✅ Outputs generated and saved

---

## Troubleshooting Guide

### Issue 1: Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'openpyxl'`

**Solution**:
```bash
pip install openpyxl markdown
```

---

### Issue 2: PDF Conversion Fails
**Symptom**: `PDF conversion failed (pdfkit/weasyprint may not be installed)`

**Solution**:
```bash
pip install weasyprint
```

**If weasyprint fails on Windows**, try pdfkit:
```bash
pip install pdfkit
# Then download and install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
```

---

### Issue 3: Playwright Browser Not Found
**Symptom**: `Executable doesn't exist at ...`

**Solution**:
```bash
playwright install chromium
```

---

### Issue 4: Environment Variables Not Set
**Symptom**: Test shows "Mode: UNGUIDED" when expecting GUIDED

**Solution (Windows)**:
```bash
set NOTEBOOKLM_GUIDED=true
echo %NOTEBOOKLM_GUIDED%
```

**Solution (Linux/macOS)**:
```bash
export NOTEBOOKLM_GUIDED=true
echo $NOTEBOOKLM_GUIDED
```

---

## AI Agent Execution Checklist

For AI agents (Claude, Antigravity, etc.) executing these tests:

### Step-by-Step Execution Protocol

**Phase 1: Environment Verification**
```bash
# Step 1.1: Check Python version
python --version
# Expected: Python 3.8.0 or higher

# Step 1.2: Check current directory
pwd  # or 'cd' on Windows
# Expected: /path/to/NotebooklmCrawler

# Step 1.3: Verify file exists
ls examples/test_modular_system.py  # or 'dir' on Windows
# Expected: File exists
```

**Phase 2: Dependency Installation**
```bash
# Step 2.1: Install core dependencies
pip install pydantic playwright beautifulsoup4 markdown

# Step 2.2: Install optional dependencies
pip install openpyxl weasyprint

# Step 2.3: Verify installation
python -c "import pydantic, markdown, openpyxl; print('✓ Dependencies OK')"
# Expected: ✓ Dependencies OK
```

**Phase 3: Execute Basic Test**
```bash
# Step 3.1: Run basic test
python examples/test_modular_system.py

# Step 3.2: Verify output files
ls outputs/test/
# Expected: test_quiz.xlsx, test_study_guide.html, test_study_guide.pdf
```

**Phase 4: Mode-Specific Tests**
```bash
# Step 4.1: Test GUIDED mode
export NOTEBOOKLM_GUIDED=true  # or 'set' on Windows
python examples/test_modular_system.py --mode guided

# Step 4.2: Test UNGUIDED mode
export NOTEBOOKLM_GUIDED=false
python examples/test_modular_system.py --mode unguided

# Step 4.3: View examples
python examples/test_modular_system.py --examples
```

**Phase 5: Verification**
```bash
# Step 5.1: Check all output files exist
ls -R outputs/test outputs/test_workflow
# Expected: Multiple .xlsx, .html, .pdf files

# Step 5.2: Verify file sizes (should be > 0 bytes)
ls -lh outputs/test/*.xlsx
# Expected: Files with reasonable sizes (> 1KB)
```

---

## Success Metrics

### For AI Agents to Report

After running tests, report the following metrics:

1. **Test Execution Status**:
   - ✅/❌ Test 1 (Prompt Generation): PASS/FAIL
   - ✅/❌ Test 2 (Format Conversion): PASS/FAIL
   - ✅/❌ Test 3 (Workflow Simulation): PASS/FAIL

2. **File Generation Count**:
   - Excel files created: X
   - HTML files created: X
   - PDF files created: X

3. **Error Count**:
   - Import errors: X
   - Conversion errors: X
   - Runtime errors: X

4. **Mode Verification**:
   - GUIDED mode test: PASS/FAIL
   - UNGUIDED mode test: PASS/FAIL

5. **Execution Time**:
   - Total test duration: X seconds

---

## Example AI Agent Report Format

```
=== NOTEBOOKLM MODULAR SYSTEM TEST REPORT ===

Timestamp: 2024-01-30 14:30:00 UTC
Agent: Claude/Antigravity
Python Version: 3.10.5
Platform: Windows 10

--- Phase 1: Environment Setup ---
✅ Dependencies installed
✅ Working directory verified
✅ Test file exists

--- Phase 2: Basic Tests ---
✅ Test 1: Prompt Generation PASSED
✅ Test 2: Format Conversion PASSED
✅ Test 3: Workflow Simulation PASSED

--- Phase 3: Mode Tests ---
✅ GUIDED mode test PASSED
✅ UNGUIDED mode test PASSED

--- Phase 4: File Outputs ---
✅ 6 Excel files created
✅ 6 HTML files created
✅ 3 PDF files created (3 skipped - weasyprint not installed)

--- Phase 5: Error Analysis ---
⚠️  0 critical errors
⚠️  3 warnings (PDF converter not available)

Execution Time: 18.3 seconds
Overall Status: ✅ PASS

Recommendation: System ready for production use. Optional: install weasyprint for full PDF support.
```

---

## Quick Reference Commands

### Run All Tests (Default)
```bash
python examples/test_modular_system.py
```

### Test Specific Mode
```bash
python examples/test_modular_system.py --mode guided
python examples/test_modular_system.py --mode unguided
```

### View Usage Examples
```bash
python examples/test_modular_system.py --examples
```

### Clean Output Directories
```bash
# Windows
rd /s /q outputs\test outputs\test_workflow

# Linux/macOS
rm -rf outputs/test outputs/test_workflow
```

### Full System Test with Browser (Requires Manual Login)
```bash
# Set environment variables
export NOTEBOOKLM_GUIDED=true
export CR_GRADE="Grade 8"
export CR_TOPIC="Physics Gravity"

# Run main pipeline
python run.py
```

---

## End of Instructions

**Note for AI Agents**: Execute commands sequentially. Wait for each command to complete before proceeding. Capture stdout and stderr for debugging. Report any deviations from expected output immediately.
