param([Parameter(Mandatory=$true)][string]$AppPath,[string]$Python="python")
$ErrorActionPreference='Stop'
$env:GPT_SOVITS_APP=(Resolve-Path -LiteralPath $AppPath).Path
$env:PYTHONUTF8='1'
& $Python -u (Join-Path $PSScriptRoot 'app.py')
