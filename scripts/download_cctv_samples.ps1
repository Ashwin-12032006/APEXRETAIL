# Downloads sample retail CCTV clips into dashboard/assets/cctv/
# Run from repo root: .\scripts\download_cctv_samples.ps1
# If downloads fail (403), save MP4s manually — see dashboard/assets/cctv/README.md

$dest = Join-Path $PSScriptRoot "..\dashboard\assets\cctv"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$files = @{
    "entry.mp4"       = "https://assets.mixkit.co/videos/preview/mixkit-people-shopping-in-a-supermarket-40841-large.mp4"
    "main_floor.mp4"  = "https://assets.mixkit.co/videos/preview/mixkit-buyer-choosing-cosmetics-in-beauty-store-40854-large.mp4"
    "billing.mp4"     = "https://assets.mixkit.co/videos/preview/mixkit-paying-at-the-cashier-in-a-supermarket-40843-large.mp4"
}

foreach ($name in $files.Keys) {
    $out = Join-Path $dest $name
    Write-Host "Downloading $name ..."
    curl.exe -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" -o $out $files[$name]
    $len = (Get-Item $out -ErrorAction SilentlyContinue).Length
    if ($len -lt 10000) {
        Write-Warning "$name may have failed ($len bytes). Download manually from Mixkit."
    } else {
        Write-Host "OK $name ($len bytes)"
    }
}

Write-Host "Done. Refresh http://localhost:8000/"
