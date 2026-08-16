# enroll-windows.ps1 — GRID 展开包（Windows 10/11；Win7 不受官方支持，勿用）
# 用法（管理员 PowerShell）: .\enroll-windows.ps1 -Token <注册令牌> [-Repo owner/repo] [-Labels "grid,win"]
param(
  [Parameter(Mandatory=$true)][string]$Token,
  [string]$Repo = "chepin-ai/ci-control",
  [string]$Labels = "grid,win"
)
$ErrorActionPreference = "Stop"
if ($env:OS -notmatch "Windows_NT") { throw "仅 Windows" }
$ver = (Invoke-RestMethod "https://api.github.com/repos/actions/runner/releases/latest").tag_name.TrimStart('v')
$dir = "$env:USERPROFILE\actions-runner\$($Repo -replace '/','_')"
New-Item -ItemType Directory -Force -Path $dir | Set-Location
Write-Host ">> 下载 runner v$ver (win-x64)"
Invoke-WebRequest -Uri "https://github.com/actions/runner/releases/download/v$ver/actions-runner-win-x64-$ver.zip" -OutFile runner.zip
Expand-Archive runner.zip -DestinationPath . -Force; Remove-Item runner.zip
Write-Host ">> 配置: repo=$Repo labels=$Labels"
.\config.cmd --unattended --url "https://github.com/$Repo" --token $Token `
  --name "$env:COMPUTERNAME-$([int](Get-Random 9999))" --labels $Labels --work _work --replace
Write-Host ">> 安装为 Windows 服务"
.\svc.cmd install; .\svc.cmd start
Start-Sleep 5; .\svc.cmd status
Write-Host "✅ GRID 节点上线：$Repo [$Labels]"
Write-Host "核验: https://github.com/$Repo/settings/actions/runners"
