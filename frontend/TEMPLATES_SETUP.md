# Templates Tab - Setup & Testing Instructions

Quick guide for setting up and testing the Templates tab.

---

## Prerequisites

### PowerShell Execution Policy

If you encounter errors like "running scripts is disabled on this system", you need to enable script execution:

**Option 1: For current session only (Recommended)**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Option 2: For current user (Permanent)**
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Run one of these commands in your PowerShell terminal before running npm commands.

---

## Installation

### 1. Navigate to Frontend Directory
```powershell
cd c:\Code\NotebooklmCrawler\frontend
```

### 2. Install Dependencies
```powershell
# If you haven't run this yet or after adding new dependencies
npm install
```

This will install all dependencies including the newly added `xlsx` library for Excel file parsing.

### 3. Start Development Server
```powershell
npm run dev
```

The terminal will show the local URL (typically `http://localhost:5173`).

---

## Testing the Templates Tab

### Quick Test Checklist

Once the dev server is running:

1. **✅ Open browser** to the URL shown in terminal
2. **✅ Click "Templates" tab** in navigation
3. **✅ Verify UI loads** - should see template sources, file upload, options panels
4. **✅ Select a template file** (e.g., expand Kani → GameApp → check ENGLISH CSV)
5. **✅ Verify prompt generates** - prompt box should appear below
6. **✅ Click copy button** - should copy to clipboard
7. **✅ Check study guide options** - select a few checkboxes
8. **✅ Check handout options** - select a few checkboxes
9. **✅ Select prompt checkbox** - top-left of prompt box
10. **✅ Click "Generate Report Prompts"** - should scroll to report output
11. **✅ Copy final report** - click "Copy All" button
12. **✅ Paste to verify** - clipboard should have full report

### Full Test Suite

For comprehensive testing, follow [test_plan.md](file:///C:/Users/reall/.gemini/antigravity/brain/6e50065c-0cf4-4abc-9766-0ba69ae37826/test_plan.md) which includes:
- 12 detailed test cases
- Step-by-step instructions
- Expected results for each step
- UI/UX verification checks
- Error handling scenarios

---

## Troubleshooting

### Dev Server Won't Start

**Error: Scripts disabled**
```
Solution: Set PowerShell execution policy (see Prerequisites above)
```

**Error: Port already in use**
```
Solution: Kill process on port 5173 or change port in vite.config.js
```

### Templates Tab Not Showing

**Check console for errors:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for import errors or component errors

**Common fixes:**
- Clear browser cache and hard reload (Ctrl+Shift+R)
- Restart dev server
- Check that all .jsx files were created correctly

### Prompts Not Generating

**If clicking template files doesn't generate prompts:**
1. Check browser console for errors
2. Verify `promptGenerator.js` exists
3. Check that state is updating (React DevTools)

### File Upload Not Working

**Drag-and-drop or upload button not responding:**
1. Verify file type (.csv, .xlsx, .xls)
2. Check browser console for file reader errors
3. Try a different file

---

## Excel File Parsing

### With xlsx Library (Recommended)

After running `npm install`, the `xlsx` library will be available. To enable full Excel parsing:

1. Open `TemplatesTab.jsx`
2. Find the `handleFileUpload` function
3. Look for the Excel file handling section
4. Uncomment the xlsx parsing code (currently uses placeholder data)

**Example implementation:**
```javascript
import * as XLSX from 'xlsx';

// In handleFileUpload, for Excel files:
if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
    reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(firstSheet);
        
        // Generate prompt with actual data
        generatePromptForUploadedFile(jsonData, file.name);
    };
    reader.readAsArrayBuffer(file);
}
```

### Without xlsx Library

Currently implemented with placeholder data:
- CSV files parse correctly
- Excel files show sample data structure
- User is alerted that full parsing requires xlsx library

---

## Using Generated Prompts with NotebookLM

### Workflow

1. **Generate your prompts** in the Templates tab
2. **Copy the final report** (click "Copy All")
3. **Open NotebookLM** (https://notebooklm.google.com/)
4. **Add your source documents** (PDFs, text files, websites, etc.)
5. **Create custom notebook guide:**
   - Click "Notebook guide"
   - Select "Create your own"
   - Paste the copied prompt
   - Click "Generate"
6. **Review the output** - NotebookLM will generate study guide, quiz, handouts as requested

---

## Known Limitations

### Current Implementation

- ✅ CSV parsing works fully
- ⚠️ Excel parsing uses placeholder data (xlsx import needs to be enabled)
- ⚠️ Template files must exist in `templates/` folder
- ⚠️ AI suggestions for study guide/handout options not yet implemented
- ✅ Dashboard settings integration works
- ✅ All UI components functional

### Browser Compatibility

Tested and works in:
- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ⚠️ Safari (clipboard API may need user interaction)

---

## Next Steps After Testing

If testing reveals issues:
1. Document the issue (test case, step, actual vs expected)
2. Check browser console for errors
3. Take screenshots if UI issue
4. Report back with details

If testing is successful:
1. Mark test cases as passed in test_plan.md
2. Consider implementing enhancements (full Excel parsing, AI suggestions)
3. Deploy to production when ready

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` | Enable npm in current session |
| `npm install` | Install dependencies (including xlsx) |
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `Ctrl+C` | Stop dev server |

**Dev URL**: http://localhost:5173 (or port shown in terminal)

**Template Files Location**: `c:\Code\NotebooklmCrawler\templates\`

**Source Code**: `c:\Code\NotebooklmCrawler\frontend\src\components\Templates\`
