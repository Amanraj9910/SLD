# PowerShell script to restart the backend server
# Handles graceful shutdown and restart of the SLD backend

param(
    [string]$BackendPath = "web_app\core\backend",
    [int]$Port = 8000,
    [switch]$Force
)

Write-Host "🔄 SLD Backend Server Restart Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Function to find and kill processes on a specific port
function Stop-ProcessOnPort {
    param([int]$Port)
    
    Write-Host "🔍 Checking for processes on port $Port..." -ForegroundColor Yellow
    
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
                    Select-Object -ExpandProperty OwningProcess | 
                    Sort-Object -Unique
        
        if ($processes) {
            foreach ($processId in $processes) {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "🛑 Stopping process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Red
                    
                    if ($Force) {
                        Stop-Process -Id $processId -Force
                    } else {
                        # Try graceful shutdown first
                        $process.CloseMainWindow()
                        Start-Sleep -Seconds 3
                        
                        # Force kill if still running
                        if (!$process.HasExited) {
                            Stop-Process -Id $processId -Force
                        }
                    }
                }
            }
            
            # Wait for processes to fully terminate
            Start-Sleep -Seconds 2
            Write-Host "✅ Processes stopped" -ForegroundColor Green
        } else {
            Write-Host "ℹ️  No processes found on port $Port" -ForegroundColor Blue
        }
    }
    catch {
        Write-Host "⚠️  Error checking port $Port`: $_" -ForegroundColor Yellow
    }
}

# Function to check if Python is available
function Test-PythonAvailable {
    $pythonCommands = @("python", "py", "python3")
    
    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Found Python: $cmd ($version)" -ForegroundColor Green
                return $cmd
            }
        }
        catch {
            # Continue to next command
        }
    }
    
    # Try common installation paths
    $commonPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            try {
                $version = & $path --version 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Found Python: $path ($version)" -ForegroundColor Green
                    return $path
                }
            }
            catch {
                # Continue to next path
            }
        }
    }
    
    return $null
}

# Function to start the backend server
function Start-BackendServer {
    param([string]$PythonCmd, [string]$BackendPath)
    
    Write-Host "🚀 Starting backend server..." -ForegroundColor Green
    
    # Change to backend directory
    $originalLocation = Get-Location
    
    try {
        if (!(Test-Path $BackendPath)) {
            throw "Backend path not found: $BackendPath"
        }
        
        Set-Location $BackendPath
        
        # Check if main.py exists
        if (!(Test-Path "main.py")) {
            throw "main.py not found in $BackendPath"
        }
        
        # Start the server in a new window
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = "cmd.exe"
        $startInfo.Arguments = "/c start `"SLD Backend Server`" cmd /k `"title SLD Backend Server && echo ======================================== && echo   SLD Backend Server && echo ======================================== && echo Backend: http://localhost:$Port && echo API Docs: http://localhost:$Port/docs && echo Health: http://localhost:$Port/health && echo. && `"$PythonCmd`" main.py`""
        $startInfo.UseShellExecute = $true
        $startInfo.WorkingDirectory = (Get-Location).Path
        
        $process = [System.Diagnostics.Process]::Start($startInfo)
        
        Write-Host "✅ Backend server started in new window" -ForegroundColor Green
        Write-Host "📡 Backend URL: http://localhost:$Port" -ForegroundColor Cyan
        Write-Host "📖 API Docs: http://localhost:$Port/docs" -ForegroundColor Cyan
        Write-Host "❤️  Health Check: http://localhost:$Port/health" -ForegroundColor Cyan
        
        return $true
    }
    catch {
        Write-Host "❌ Failed to start backend server: $_" -ForegroundColor Red
        return $false
    }
    finally {
        Set-Location $originalLocation
    }
}

# Function to test server health
function Test-ServerHealth {
    param([int]$Port, [int]$MaxAttempts = 10)
    
    Write-Host "🔍 Testing server health..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$Port/health" -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ Server is healthy!" -ForegroundColor Green
                return $true
            }
        }
        catch {
            Write-Host "⏳ Attempt $i/$MaxAttempts - Server not ready yet..." -ForegroundColor Yellow
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Host "⚠️  Server health check failed after $MaxAttempts attempts" -ForegroundColor Yellow
    return $false
}

# Main execution
try {
    # Step 1: Stop existing processes
    Write-Host "🛑 Step 1: Stopping existing backend processes" -ForegroundColor Magenta
    Stop-ProcessOnPort -Port $Port
    
    # Step 2: Check Python availability
    Write-Host "🐍 Step 2: Checking Python availability" -ForegroundColor Magenta
    $pythonCmd = Test-PythonAvailable
    
    if (!$pythonCmd) {
        Write-Host "❌ Python not found! Please install Python and ensure it's in your PATH." -ForegroundColor Red
        Write-Host "💡 You can download Python from: https://python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    
    # Step 3: Start backend server
    Write-Host "🚀 Step 3: Starting backend server" -ForegroundColor Magenta
    $started = Start-BackendServer -PythonCmd $pythonCmd -BackendPath $BackendPath
    
    if (!$started) {
        Write-Host "❌ Failed to start backend server" -ForegroundColor Red
        exit 1
    }
    
    # Step 4: Wait and test health
    Write-Host "⏳ Step 4: Waiting for server to initialize..." -ForegroundColor Magenta
    Start-Sleep -Seconds 5
    
    $healthy = Test-ServerHealth -Port $Port
    
    if ($healthy) {
        Write-Host "🎉 Backend server restart completed successfully!" -ForegroundColor Green
        Write-Host "🌐 You can now access the backend at http://localhost:$Port" -ForegroundColor Cyan
    } else {
        Write-Host "⚠️  Backend server started but health check failed" -ForegroundColor Yellow
        Write-Host "💡 Check the server window for any error messages" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Restart script failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Restart script completed" -ForegroundColor Green
