<#
==============================================================================
Network Control Plane — Edge Host Agent Automated Installer (Windows PowerShell)
Product: Network Control Plane
==============================================================================
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ControlPlane,

    [Parameter(Mandatory=$true)]
    [string]$Token,

    [Parameter(Mandatory=$false)]
    [string]$Runtime = "auto"
)

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   Network Control Plane — Remote Host Agent Installer (Windows)" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$ControlPlane = $ControlPlane.TrimEnd('/')
$Hostname = $env:COMPUTERNAME.ToLower()
$Arch = if ([Environment]::Is64BitOperatingSystem) { "x86_64" } else { "x86" }

$DetectedRuntime = $Runtime
if ($DetectedRuntime -eq "auto") {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $DetectedRuntime = "docker"
    } elseif (Get-Command Get-VMSwitch -ErrorAction SilentlyContinue) {
        $DetectedRuntime = "hyperv"
    } else {
        $DetectedRuntime = "docker"
    }
}

Write-Host "[*] Host: $Hostname ($Arch) | Target Runtime: $DetectedRuntime" -ForegroundColor Gray
Write-Host "[*] Enrolling node with Network Control Plane at $ControlPlane..." -ForegroundColor Yellow

$Payload = @{
    bootstrap_token = $Token
    hostname = $Hostname
    provider_type = $DetectedRuntime
    os = "windows"
    architecture = $Arch
    environment = "production"
} | ConvertTo-Json

$EnrollUrl = "$ControlPlane/api/v1/agent/enroll"
try {
    $Response = Invoke-RestMethod -Uri $EnrollUrl -Method Post -Body $Payload -ContentType "application/json"
    $HostId = $Response.host_id
    $ApiToken = $Response.api_token
    Write-Host "[✓] Enrolled Successfully! Assigned Host ID: $HostId" -ForegroundColor Green
} catch {
    Write-Error "[-] Enrollment failed: $_"
    exit 1
}

$ConfigDir = "C:\ProgramData\NetworkControlPlaneAgent"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}

$ConfigFile = Join-Path $ConfigDir "config.json"
@{
    host_id = $HostId
    control_plane_url = $ControlPlane
    api_token = $ApiToken
    runtime = $DetectedRuntime
} | ConvertTo-Json | Set-Content -Path $ConfigFile

Write-Host "[*] Configuration written to $ConfigFile" -ForegroundColor Gray
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " [✓] Onboarding Complete! Node '$HostId' is connected to NCP." -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
