# SupeRR Intelligence — Local Start Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SupeRR Intelligence — Cricket Scouting & Auction Engine" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check if data exists
if (-not (Test-Path "data/app/analytics.duckdb")) {
    Write-Host "Initializing analytics pipeline..." -ForegroundColor Yellow
    python -m backend.analytics.ingestion.run
    python -m backend.analytics.state.build_states
    python -m backend.analytics.train.run_all
    python -m backend.analytics.ranking.build
    python -m backend.analytics.export.build_dashboard_tables
}

Write-Host "`nStarting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
}

Write-Host "Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Green
Set-Location "frontend"
npm run dev

# Stop backend job on exit
Stop-Job $backendJob
Remove-Job $backendJob
