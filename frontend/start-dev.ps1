# Set PowerShell execution policy for current session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

Write-Host "✅ PowerShell execution policy set for this session" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Installing dependencies (including xlsx library)..." -ForegroundColor Cyan
npm install

Write-Host ""
Write-Host "🚀 Starting development server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
npm run dev
