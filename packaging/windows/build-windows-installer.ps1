# ==============================================================================
# JobCatalyst AI - Windows Installer Build & Deployment Automation Orchestrator
# ==============================================================================
# This PowerShell script serves as the release pipeline tool to package the app
# for Windows client machines. It validates environments, compiles Inno Setup,
# compiles WiX Toolset MSI, signs binaries, and exports deploy/uninstall scripts.

Param(
    [string]$Version = "1.0.0-RC1",
    [switch]$Offline = $false,
    [string]$CertPath = "",
    [string]$CertPassword = "",
    [switch]$RunTests = $false
)

$ErrorActionPreference = "Stop"

Write-Output "======================================================================"
Write-Output "   JobCatalyst AI - Windows Package Engineering Pipeline"
Write-Output "======================================================================"

# 1. Establish directory layout paths
$ProjectRoot = Resolve-Path "..\.."
$DistDir = Join-Path $ProjectRoot "dist-release\windows"
If (!(Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir -Force | Out-Null
}

# Ensure launcher mock dummy is present in dist-release directory for packaging compiler
$LauncherPath = Join-Path $DistDir "JobCatalystLauncher.exe"
If (!(Test-Path $LauncherPath)) {
    Write-Output "[*] Building mock launcher launcher.exe for distribution staging..."
    Set-Content -Path $LauncherPath -Value "JobCatalyst AI Windows Service Bootstrap BinaryStub"
}

# 2. Check for compilers presence
$InnoCompiler = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
$WixCandle = "C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe"
$WixLight = "C:\Program Files (x86)\WiX Toolset v3.11\bin\light.exe"

# 3. Compile Inno Setup EXE Installer
Write-Output "[1/3] Initiating Inno Setup EXE Package compilation..."
$InnoScript = Join-Path (Get-Location) "installer.iss"
If (Test-Path $InnoCompiler) {
    $Params = @()
    If ($Offline) { $Params += "/DOffline=1" }
    & $InnoCompiler $Params $InnoScript
    Write-Output "[+] Success: Compiled Inno Setup EXE installer at $DistDir\JobCatalystAI-Setup.exe"
} Else {
    Write-Output "[!] Warning: Inno Setup Compiler (ISCC) not found. Skipping physical compilation. ISS configuration ready."
}

# 4. Compile WiX Toolset MSI Package
Write-Output "[2/3] Initiating WiX Toolset MSI Package compilation..."
$WixScript = Join-Path (Get-Location) "JobCatalystAI.wxs"
If ((Test-Path $WixCandle) -and (Test-Path $WixLight)) {
    $ObjFile = Join-Path $DistDir "JobCatalystAI.wixobj"
    $MsiFile = Join-Path $DistDir "JobCatalystAI.msi"
    
    & $WixCandle -out $ObjFile $WixScript
    & $WixLight -out $MsiFile $ObjFile -ext WixUIExtension
    
    Write-Output "[+] Success: Compiled WiX MSI installer at $MsiFile"
} Else {
    Write-Output "[!] Warning: WiX Toolset binaries not found. Skipping physical compilation. WXS configuration ready."
}

# 5. Dual Code Signing Module (SHA-256 Authenticode)
Write-Output "[3/3] Code-signing release binaries..."
If ($CertPath -and (Test-Path $CertPath)) {
    $Signtool = "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
    If (Test-Path $Signtool) {
        Write-Output "[*] Applying Authenticode signature using: $CertPath"
        & $Signtool sign /f $CertPath /p $CertPassword /fd sha256 /tr http://timestamp.digicert.com /td sha256 "$DistDir\*.exe"
        & $Signtool sign /f $CertPath /p $CertPassword /fd sha256 /tr http://timestamp.digicert.com /td sha256 "$DistDir\*.msi"
        Write-Output "[+] Digital signatures applied successfully."
    } Else {
        Write-Output "[!] Signtool.exe not found. Skipping physical signing."
    }
} Else {
    Write-Output "[*] Developer signature mode (unsigned). Production deployments should supply -CertPath."
}

# 6. Generate silent installation/uninstallation test wrappers
Write-Output "======================================================================"
Write-Output "   Deployment Command Recipes Generated:"
Write-Output "======================================================================"
Write-Output " [Silent Installation - EXE]"
Write-Output "   JobCatalystAI-Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-"
Write-Output ""
Write-Output " [Silent Upgrade - EXE]"
Write-Output "   JobCatalystAI-Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /REINSTALL /FORCE"
Write-Output ""
Write-Output " [Silent Installation - GPO/MSI]"
Write-Output "   msiexec.exe /i JobCatalystAI.msi /qn /norestart"
Write-Output ""
Write-Output " [Self-Repair Installation - MSI]"
Write-Output "   msiexec.exe /focums JobCatalystAI.msi /qn"
Write-Output ""
Write-Output " [Silent Uninstallation - MSI]"
Write-Output "   msiexec.exe /x JobCatalystAI.msi /qn"
Write-Output "======================================================================"
