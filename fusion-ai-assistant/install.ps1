# Fusion AI Assistant - Install Script (UTF-8 with BOM)
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

Write-Host ''
Write-Host '====================================' -ForegroundColor Cyan
Write-Host '  Fusion AI Assistant - Installer' -ForegroundColor Cyan
Write-Host '====================================' -ForegroundColor Cyan
Write-Host ''

# Candidate Fusion AddIns paths (priority order)
$candidate_paths = @(
    "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns",
    "$env:APPDATA\Autodesk\Fusion 360\API\AddIns",
    "$env:LOCALAPPDATA\Autodesk\Autodesk Fusion 360\API\AddIns"
)

$target_dir = $null
foreach ($p in $candidate_paths) {
    if (Test-Path $p) {
        $target_dir = $p
        Write-Host "[OK] Found Fusion AddIns: $p" -ForegroundColor Green
        break
    }
}

if (-not $target_dir) {
    $target_dir = $candidate_paths[0]
    Write-Host "[!] AddIns dir not found, creating: $target_dir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $target_dir | Out-Null
}

$link_path = Join-Path $target_dir "FusionAIAssistant"
$source_path = $PSScriptRoot

# Check existing
if (Test-Path $link_path) {
    $item = Get-Item $link_path
    $isLink = $item.Attributes -band [System.IO.FileAttributes]::ReparsePoint
    if ($isLink) {
        Write-Host "[!] Existing symlink found, removing..." -ForegroundColor Yellow
        (Get-Item $link_path).Delete()
    } else {
        Write-Host "[!] Existing folder found at target" -ForegroundColor Yellow
        Write-Host "    Manually remove or rename: $link_path" -ForegroundColor Yellow
        exit 1
    }
}

# Copy or symlink
$useSymlink = $false
try {
    New-Item -ItemType SymbolicLink -Path $link_path -Target $source_path -ErrorAction Stop | Out-Null
    $useSymlink = $true
    Write-Host "[OK] Created symbolic link" -ForegroundColor Green
} catch {
    Write-Host "[!] Symlink failed (need admin?), falling back to copy..." -ForegroundColor Yellow
    Copy-Item -Path $source_path -Destination $link_path -Recurse -Force
    Write-Host "[OK] Copied files instead" -ForegroundColor Green
}

Write-Host ""
Write-Host "  Location: $link_path"
Write-Host "  Source:   $source_path"
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  1. Restart Fusion 360"
Write-Host "  2. Tools -> Scripts and Add-Ins"
Write-Host "  3. Find [FusionAIAssistant] -> click [Run]"
Write-Host ""
Write-Host "  Tip: edit config.json to set your Mavis session ID" -ForegroundColor Yellow
Write-Host ""