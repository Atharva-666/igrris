# start.ps1
# This script starts BOTH the FastAPI backend and the Nuxt frontend in parallel.

$scriptPath = $MyInvocation.MyCommand.Path
$rootDir = Split-Path $scriptPath

Set-Location $rootDir

Write-Host "Cleaning up any previously orphaned processes..." -ForegroundColor Yellow
$portsToClear = @(8000, 8501)
foreach ($port in $portsToClear) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Killing process $($proc.Name) (PID: $($proc.Id)) on port $port..." -ForegroundColor DarkYellow
            $proc | Stop-Process -Force
        }
    }
}

Write-Host "`nStarting Igrris AI..." -ForegroundColor Cyan

# 1. Start the FastAPI Backend on port 8000 (Hidden/Background)
Write-Host "Starting FastAPI backend on port 8000..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "$rootDir\venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "backend.igrris_api:app", "--host", "0.0.0.0", "--port", "8000" -PassThru -WindowStyle Hidden

# Give backend a moment to boot
Start-Sleep -Seconds 3

try {
    # 2. Start the Nuxt Frontend on port 8501 (Foreground)
    Write-Host "Starting Nuxt frontend on port 8501..." -ForegroundColor Green
    Set-Location "$rootDir\frontend-web"
    npm run dev -- --port 8501
} finally {
    # When the user stops Nuxt (Ctrl+C), clean up the backend process
    Write-Host "`nShutting down servers..." -ForegroundColor Yellow
    if ($backendProcess -and !$backendProcess.HasExited) {
        $backendProcess | Stop-Process -Force
    }
    
    # Force kill anything still holding our ports to guarantee clean exit
    foreach ($port in $portsToClear) {
        $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        foreach ($conn in $connections) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                $proc | Stop-Process -Force
            }
        }
    }
    Write-Host "All processes stopped successfully." -ForegroundColor Green
}
