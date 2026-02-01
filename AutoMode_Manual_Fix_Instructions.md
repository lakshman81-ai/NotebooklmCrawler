# AutoMode.jsx Manual Fix Instructions

## Problem
The file has been corrupted with ``` at line 1 and needs to be fixed before we can continue.

## Quick Fix Steps

### Option 1: Use PowerShell to Remove Line 1

```powershell
# Navigate to the frontend directory
cd c:\Code\NotebooklmCrawler\frontend\src\components\Dashboard

# Remove the first line (```) from AutoMode.jsx
(Get-Content AutoMode.jsx | Select-Object -Skip 1) | Set-Content AutoMode.jsx.fixed
Remove-Item AutoMode.jsx
Rename-Item AutoMode.jsx.fixed AutoMode.jsx
```

### Option 2: Manual Editor Fix

1. Open `c:\Code\NotebooklmCrawler\frontend\src\components\Dashboard\AutoMode.jsx` in your editor
2. **Delete line 1** (the line with just ```)
3. Save the file

The file should start with:
```javascript
import React, { useState, useEffect } from 'react';
import { Play, ShieldCheck, Activity, Terminal, Globe, Bot, Download, Check, Link as LinkIcon, Search, Layers, FileText, Cpu, Zap, AlertCircle, AlertTriangle, CheckCircle, BookOpen, HelpCircle, Layout, ClipboardList, Folder, ChevronRight, X, Copy, StickyNote, Clipboard } from 'lucide-react';
```

---

## Then: Remove Settings/User Icons (Phase 2.1)

After fixing the ``` issue, you need to remove these sections:

### 1. Find and Remove Settings/User Icons (around line 496-507)

Look for this code block and **DELETE IT**:
```javascript
{/* Settings Group (Bottom) */}
<div className="w-full space-y-4 mb-4">
    <button
        onClick={() => setShowSettings(!showSettings)}
        className={`mx-auto p-3 rounded-xl transition-all ${showSettings ? 'bg-indigo-900 text-indigo-400' : 'bg-slate-900 text-slate-500 hover:text-indigo-400 hover:bg-slate-800'}`}
    >
        <Settings className="w-5 h-5" />
    </button>
    <div className="mx-auto p-3 rounded-xl bg-slate-900 text-slate-600">
        <User className="w-5 h-5" />
    </div>
</div>
```

### 2. Remove Settings Overlay (around line 510-650)

Look for and **DELETE THIS ENTIRE BLOCK**:
```javascript
{/* --- Settings Overlay (Config) --- */}
{showSettings && (
    <div className="absolute left-24 bottom-24 bg-white...">
        {/* ... entire settings panel ... */}
    </div>
)}
```

It ends with the closing `)}` after the "Save Configuration" button.

### 3. Remove showSettings State (around line 252)

Find and **DELETE**:
```javascript
const [showSettings, setShowSettings] = useState(false);
```

But **KEEP**:
```javascript
const [logs, setLogs] = useState([]);
const [guidedPopupOpen, setGuidedPopupOpen] = useState(false);
```

### 4. Update Imports (line 2)

Change FROM:
```javascript
import { Play, ShieldCheck, Activity, Terminal, Globe, Bot, Download, Check, Link as LinkIcon, Search, Layers, FileText, Cpu, Zap, AlertCircle, AlertTriangle, CheckCircle, BookOpen, HelpCircle, Layout, ClipboardList, Settings, User, Folder, ChevronRight, X, Copy, StickyNote, Clipboard } from 'lucide-react';
```

TO (remove `Settings, User`):
```javascript
import { Play, ShieldCheck, Activity, Terminal, Globe, Bot, Download, Check, Link as LinkIcon, Search, Layers, FileText, Cpu, Zap, AlertCircle, AlertTriangle, CheckCircle, BookOpen, HelpCircle, Layout, ClipboardList, Folder, ChevronRight, X, Copy, StickyNote, Clipboard } from 'lucide-react';
```

---

## Verification

After making these changes:

1. Check that the file has NO lint errors
2. The file should start with `import React` (no ``` before it)
3. No `Settings` or `User` icons in the imports
4. No floating Settings/User buttons in the sidebar
5. No Settings overlay panel

---

## When Ready

After you've completed these manual fixes, let me know and I'll continue with:
- **Phase 3**: Create Logging Service + Logs Tab
- **Phase 4**: Config Consolidation  
- **Phase 5**: UI Optimization for 15" laptops
