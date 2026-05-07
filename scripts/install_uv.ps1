[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

try {
    # 1. Kiem tra xem may da co uv Global chua
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        Write-Host "    - [OK] Phat hien ban uv Global tren he thong."
        exit 2  # Thoat voi ma 2 de bao cho .bat biet la dung Global
    }

    # Khai bao thu muc cache co dinh cua app
    $appCacheDir = "$env:USERPROFILE\SportSeeker\bin"
    $cachedUvPath = "$appCacheDir\uv.exe"

    # 2. Kiem tra xem uv.exe da co trong Cache chua
    if (Test-Path $cachedUvPath) {
        Write-Host "    - [OK] Phat hien uv tai Cache ($cachedUvPath)."
        exit 0  # Thoat voi ma 0 de bao cho .bat biet la dung Cache
    }

    # 3. Neu chua co gi ca -> Tao thu muc va Tai moi
    if (-not (Test-Path $appCacheDir)) {
        New-Item -ItemType Directory -Path $appCacheDir -Force | Out-Null
    }

    Write-Host "    - Dang ket noi de tai uv..."
    $zipUrl = "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
    Invoke-WebRequest -Uri $zipUrl -OutFile "uv.zip" -UseBasicParsing

    Write-Host "    - Dang giai nen..."
    Expand-Archive -Path "uv.zip" -DestinationPath "uv_tmp" -Force

    Write-Host "    - Dang luu uv vao Cache..."
    Copy-Item -Path "uv_tmp\uv.exe" -Destination $cachedUvPath -Force

    Write-Host "    - Dang don dep file tam..."
    Remove-Item -Path "uv_tmp" -Recurse -Force
    Remove-Item -Path "uv.zip" -Force

    Write-Host "    - [OK] uv da san sang hoat dong."
    exit 0  # Thoat voi ma 0 (Thanh cong, dung Cache)

} catch {
    Write-Host ""
    Write-Host "========================================================"
    Write-Host "[LOI] Phat hien loi trong qua trinh thiet lap uv!"
    Write-Host "Chi tiet loi: $($_.Exception.Message)"
    Write-Host "========================================================"
    exit 1  # Thoat voi ma 1 (Loi)
}
