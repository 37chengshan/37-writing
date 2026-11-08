#Requires -Version 5.1
<#
.SYNOPSIS
  Install Chinese Humanizer Writer Skill for Claude Code and/or Codex on Windows.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target Both -Scope User -DryRun
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Target ClaudeCode -Scope Project -ProjectPath 'C:\my-project'
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet('ClaudeCode', 'Codex', 'Both')]
    [string]$Target = 'ClaudeCode',
    [ValidateSet('User', 'Project')]
    [string]$Scope = 'User',
    [string]$ProjectPath = '.',
    [switch]$Force,
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) {
    throw 'Invalid skill package: missing SKILL.md'
}
$root = if ($Scope -eq 'User') { $HOME } else { (Resolve-Path -LiteralPath $ProjectPath).Path }
$targets = if ($Target -eq 'Both') { @('ClaudeCode', 'Codex') } else { @($Target) }
foreach ($t in $targets) {
    if ($t -eq 'ClaudeCode') {
        $parent = Join-Path (Join-Path $root '.claude') 'skills'
    } else {
        $parent = Join-Path (Join-Path $root '.agents') 'skills'
    }
    $dest = Join-Path $parent 'chinese-humanizer-writer'
    if ([System.IO.Path]::GetFullPath($dest).TrimEnd('\') -ieq [System.IO.Path]::GetFullPath($source).TrimEnd('\')) {
        Write-Host "Already installed at source location: $dest"
        continue
    }
    if (Test-Path -LiteralPath $dest) {
        if (-not $Force) {
            throw "Target exists: $dest. Use -Force to backup old installation first."
        }
        $backup = "$dest.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        if (Test-Path -LiteralPath $backup) { throw "Backup already exists: $backup" }
        if ($DryRun) { Write-Host "[DRY-RUN] Would backup $dest -> $backup" }
        elseif ($PSCmdlet.ShouldProcess($dest, "Move existing skill to $backup")) {
            Move-Item -LiteralPath $dest -Destination $backup
        }
    }
    if ($DryRun) {
        Write-Host "[DRY-RUN] Would install $source -> $dest"
        continue
    }
    if ($PSCmdlet.ShouldProcess($dest, 'Install writing skill')) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        Copy-Item -LiteralPath $source -Destination $dest -Recurse -Force
        Write-Host "Installed: $dest"
    }
}
Write-Host 'Restart your agent/terminal if it caches available skills. No platform accounts were accessed.'
