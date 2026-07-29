<#
.SYNOPSIS
    Horizon news fetcher script
.PARAMETER Topic
    ai or unity
.EXAMPLE
    .\run-horizon.ps1 -Topic ai
    .\run-horizon.ps1 -Topic unity
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("ai","unity")]
    [string]$Topic
)

$ErrorActionPreference = "Stop"
$HorizonDir = "$PSScriptRoot\.horizon"
$Date = Get-Date -Format "yyyy-MM-dd"
$UvPath = "C:\Users\李超超\新建文件夹\Scripts\uv.exe"
if (-not (Test-Path $UvPath)) {
    $UvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
}
Write-Host "  UV path: $UvPath"

Write-Host "[1/4] Switching config: $Topic" -ForegroundColor Cyan
$configSrc = "$HorizonDir\data\config-$Topic.json"
$configDst = "$HorizonDir\data\config.json"
Copy-Item $configSrc $configDst -Force
Write-Host "  Loaded config-$Topic.json"

Write-Host "[2/4] Starting Horizon..." -ForegroundColor Cyan
Push-Location $HorizonDir
try {
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    & $UvPath run horizon $args
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Horizon exited with code: $LASTEXITCODE" -ForegroundColor Yellow
    }
} finally {
    Pop-Location
}

Write-Host "[3/4] Copying reports to knowledge base..." -ForegroundColor Cyan
$summariesDir = "$HorizonDir\data\summaries"

if ($Topic -eq "ai") {
    $targetDir = (Get-ChildItem -Path $PSScriptRoot -Directory -Filter "01-AI*")[0].FullName + "\raw"
} else {
    $targetDir = (Get-ChildItem -Path $PSScriptRoot -Directory -Filter "02-Unity*")[0].FullName + "\raw"
}

$zhReport = ""
if (Test-Path $summariesDir) {
    $files = Get-ChildItem "$summariesDir\horizon-$Date-*.md" -ErrorAction SilentlyContinue
    if ($files) {
        foreach ($f in $files) {
            $newName = "$Date-$Topic-daily-$($f.Name)"
            $destPath = Join-Path $targetDir $newName
            Copy-Item $f.FullName $destPath -Force
            Write-Host "  Saved: $newName" -ForegroundColor Green
            if ($f.Name -match "-zh\.md$") {
                $zhReport = $destPath
            }
        }
    } else {
        Write-Host "  No report generated today (possibly no high-score content)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Summaries directory not found" -ForegroundColor Yellow
}

Write-Host "[4/4] Pushing condensed report to WeChat..." -ForegroundColor Cyan
if ($zhReport -and (Test-Path $zhReport)) {
    $envFile = "$HorizonDir\.env"
    $pushToken = ""
    $deepseekKey = ""
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^PUSHPLUS_TOKEN=(.+)$') {
                $pushToken = $Matches[1].Trim()
            }
            if ($_ -match '^DEEPSEEK_API_KEY=(.+)$') {
                $deepseekKey = $Matches[1].Trim()
            }
        }
    }
    if ($pushToken) {
        Push-Location $HorizonDir
        try {
            $env:PYTHONUTF8 = "1"
            & $UvPath run python push_report.py $zhReport $Topic $pushToken $deepseekKey
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "  PUSHPLUS_TOKEN not set, skip push" -ForegroundColor Yellow
    }
} else {
    Write-Host "  No ZH report found, skip push" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "  Date: $Date"
Write-Host "  Topic: $Topic"
Write-Host "  Saved to: $targetDir"
Write-Host ""
Write-Host "Tip: Tell Trae AI to 'organize $Topic raw folder' to extract knowledge pages" -ForegroundColor Cyan
