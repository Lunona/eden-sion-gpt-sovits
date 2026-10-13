param([string]$AppPath='',[string]$Python='',[switch]$Stop,[switch]$NoBrowser)
$ErrorActionPreference='Stop'
try {
    $taskSettings=Join-Path $PSScriptRoot 'launcher-settings.json'
    if (Test-Path -LiteralPath $taskSettings) {
        $taskConfig=Get-Content -LiteralPath $taskSettings -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $AppPath) { $AppPath=$taskConfig.app }
        if (-not $Python) { $Python=$taskConfig.python }
    }
    if (-not $AppPath) { $AppPath=Read-Host '首次使用：请输入已安装的 GPT-SoVITS 目录（可直接粘贴路径）' }
    $AppPath=$AppPath.Trim().Trim('"')
    $AppPath=(Resolve-Path -LiteralPath $AppPath).Path
    if (Test-Path -LiteralPath (Join-Path $AppPath 'app\GPT_SoVITS\inference_webui.py')) { $AppPath=Join-Path $AppPath 'app' }
    if (-not (Test-Path -LiteralPath (Join-Path $AppPath 'GPT_SoVITS\inference_webui.py'))) { throw '目录里没有 GPT_SoVITS\inference_webui.py，请填写完整环境的程序目录。' }
    if (-not $Python) {
        $taskParent=Split-Path -Parent $AppPath
        $taskCandidates=@((Join-Path $AppPath 'runtime\python.exe'),(Join-Path $AppPath 'venv\Scripts\python.exe'),(Join-Path $taskParent 'venv\Scripts\python.exe'),(Join-Path $taskParent 'runtime\python.exe'))
        $Python=$taskCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }
    if (-not $Python) { $Python=Read-Host '未找到环境 Python，请输入完整环境中 python.exe 的路径' }
    $Python=$Python.Trim().Trim('"')
    $Python=(Resolve-Path -LiteralPath $Python).Path
    @{app=$AppPath;python=$Python} | ConvertTo-Json | Set-Content -LiteralPath $taskSettings -Encoding UTF8
    $env:PYTHONUTF8='1'
    $taskMode=if($Stop){'stop'}else{'start'}
    $taskArguments=@('-X','utf8','-u',(Join-Path $PSScriptRoot 'unified_controller.py'),$taskMode,'--app',$AppPath)
    if($NoBrowser){$taskArguments+='--no-browser'}
    & $Python @taskArguments
    if($LASTEXITCODE -ne 0){throw '运行失败，请检查上面的提示及 launcher-logs 文件夹。'}
    if(-not $NoBrowser){Read-Host '按回车关闭此窗口'}
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    if(-not $NoBrowser){Read-Host '按回车关闭此窗口'}
    exit 1
}
