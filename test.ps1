# Run pytest on the enikk project
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot

Write-Host "--- pytest ---"
.\.venv\Scripts\python.exe -m pytest tests/ -v @args

Pop-Location