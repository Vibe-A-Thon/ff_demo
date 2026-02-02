#!/usr/bin/env pwsh
# Production Build Script for Fraud Forge Frontend
# This script builds and optimizes the React frontend for production deployment

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Production Build Process..." -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
$FRONTEND_DIR = Join-Path $PSScriptRoot ".." "frontend"
Set-Location $FRONTEND_DIR

# 1. Clean previous build
Write-Host "🧹 Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "✅ Removed old build directory" -ForegroundColor Green
}

# 2. Install dependencies (if needed)
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Dependency installation failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}

# 3. Run production build
Write-Host ""
Write-Host "⚙️  Building production bundle..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray

$env:NODE_ENV = "production"
$env:GENERATE_SOURCEMAP = "true"  # Enable source maps for debugging
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host"❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Build completed successfully!" -ForegroundColor Green

# 4. Analyze bundle size
Write-Host ""
Write-Host "📊 Build Statistics:" -ForegroundColor Cyan

$BUILD_DIR = Join-Path $FRONTEND_DIR "build"
$STATIC_DIR = Join-Path $BUILD_DIR "static"

# Get total build size
$totalSize = (Get-ChildItem -Path $BUILD_DIR -Recurse | Measure-Object -Property Length -Sum).Sum
$totalSizeMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "   Total Build Size: $totalSizeMB MB" -ForegroundColor White

# Get JS bundle sizes
if (Test-Path (Join-Path $STATIC_DIR "js")) {
    Write-Host ""
    Write-Host "   JavaScript Bundles:" -ForegroundColor White
    Get-ChildItem -Path (Join-Path $STATIC_DIR "js") -Filter "*.js" | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1KB, 2)
        $name = $_.Name
        Write-Host "     - $name : $sizeMB KB" -ForegroundColor Gray
    }
}

# Get CSS bundle sizes
if (Test-Path (Join-Path $STATIC_DIR "css")) {
    Write-Host ""
    Write-Host "   CSS Bundles:" -ForegroundColor White
    Get-ChildItem -Path (Join-Path $STATIC_DIR "css") -Filter "*.css" | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1KB, 2)
        $name = $_.Name
        Write-Host "     - $name : $sizeMB KB" -ForegroundColor Gray
    }
}

# 5. Optional: Compress build (gzip)
Write-Host ""
Write-Host "🗜️  Compressing assets..." -ForegroundColor Yellow

$compressedCount = 0

# Compress JS files
Get-ChildItem -Path (Join-Path $STATIC_DIR "js") -Filter "*.js" -ErrorAction SilentlyContinue | ForEach-Object {
    $gzipPath = "$($_.FullName).gz"
    $inputStream = [System.IO.File]::OpenRead($_.FullName)
    $outputStream = [System.IO.File]::Create($gzipPath)
    $gzipStream = New-Object System.IO.Compression.GZipStream($outputStream, [System.IO.Compression.CompressionMode]::Compress)
    $inputStream.CopyTo($gzipStream)
    $gzipStream.Close()
    $outputStream.Close()
    $inputStream.Close()
    $compressedCount++
}

# Compress CSS files
Get-ChildItem -Path (Join-Path $STATIC_DIR "css") -Filter "*.css" -ErrorAction SilentlyContinue | ForEach-Object {
    $gzipPath = "$($_.FullName).gz"
    $inputStream = [System.IO.File]::OpenRead($_.FullName)
    $outputStream = [System.IO.File]::Create($gzipPath)
    $gzipStream = New-Object System.IO.Compression.GZipStream($outputStream, [System.IO.Compression.CompressionMode]::Compress)
    $inputStream.CopyTo($gzipStream)
    $gzipStream.Close()
    $outputStream.Close()
    $inputStream.Close()
    $compressedCount++
}

Write-Host "✅ Compressed $compressedCount files" -ForegroundColor Green

# 6. Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎉 Production Build Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Build Directory: $BUILD_DIR" -ForegroundColor White
Write-Host "Total Size: $totalSizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Test the build: npm run serve" -ForegroundColor Gray
Write-Host "  2. Deploy via FastAPI static serving" -ForegroundColor Gray
Write-Host "  3. Or use Nginx for production" -ForegroundColor Gray
Write-Host ""
