## Quick Start Guide - Launch Server

Due to PowerShell execution policy, you need to run the server manually.

### Option 1: Fix PowerShell Policy (Recommended)

**Run PowerShell as Administrator** and execute:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then start the server:
```powershell
cd c:\Code\NotebooklmCrawler\frontend
npm run dev
```

### Option 2: Use CMD Instead

Open **Command Prompt** (not PowerShell) and run:
```cmd
cd c:\Code\NotebooklmCrawler\frontend
npm run dev
```

### Option 3: Bypass Execution Policy (One-Time)

In PowerShell:
```powershell
PowerShell -ExecutionPolicy Bypass -Command "cd c:\Code\NotebooklmCrawler\frontend; npm run dev"
```

---

## Expected Output

When the server starts successfully, you should see:

```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Then open **http://localhost:5173** in your browser.

---

## What to Test

1. **Navigation Bar** - Should show: Dashboard | Templates | Config | Logs | Admin
2. **Logs Tab** - Click it, verify log interface loads
3. **Config Tab** - Save settings, check they persist after refresh
4. **Environment Variables** - See 3 API key fields at bottom of Config tab

---

## If You See Errors

1. **"Cannot find module"** - Run `npm install` first
2. **Port 5173 in use** - Close other Vite servers or use `npm run dev -- --port 3000`
3. **PowerShell errors** - Use CMD or fix execution policy (Option 1 above)

---

## To Stop Server

Press **Ctrl + C** in the terminal
