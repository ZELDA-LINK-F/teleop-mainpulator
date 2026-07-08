# Fusion AI Assistant - Uninstall Script
# Run with: powershell -ExecutionPolicy Bypass -File uninstall.ps1

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host ''
Write-Host '====================================' -ForegroundColor Cyan
Write-Host '  Fusion AI Assistant - Uninstaller' -ForegroundColor Cyan
Write-Host '====================================' -ForegroundColor Cyan
Write-Host ''

$candidate_paths = @(
    "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns",
    "$env:APPDATA\Autodesk\Fusion 360\API\AddIns",
    "$env:LOCALAPPDATA\Autodesk\Autodesk Fusion 360\API\AddIns"
)

$link_path = $null
foreach ($p in $candidate_paths) {
    $candidate = Join-Path $p "FusionAIAssistant"
    if (Test-Path $candidate) {
        $link_path = $candidate
        break
    }
}

if (-not $link_path) {
    Write-Host "[!] Not installed, nothing to uninstall" -ForegroundColor Yellow
    exit 0
}

try {
    (Get-Item $link_path).Delete()
    Write-Host "[OK] Removed: $link_path" -ForegroundColor Green
    Write-Host ""
    Write-Host "Source files kept at: $PSScriptRoot" -ForegroundColor Cyan
    Write-Host "To fully remove: delete this folder manually" -ForegroundColor Yellow
} catch {
    Write-Host "[X] Failed: $_" -ForegroundColor Red
    Write-Host "    Try running PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}