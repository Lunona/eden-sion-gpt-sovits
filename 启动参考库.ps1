param([string]$AppPath='',[string]$Python='')
& (Join-Path $PSScriptRoot '启动诗音.ps1') -AppPath $AppPath -Python $Python
