@echo off
setlocal
set "BIN_DIR=%~dp0"
for %%I in ("%BIN_DIR%..") do set "SDK_ROOT=%%~fI"
set "REPO_ROOT=%SDK_ROOT%\.."
set "PYTHONPATH=%SDK_ROOT%;%REPO_ROOT%;%REPO_ROOT%\rcir\src;%PYTHONPATH%"
python -m polyflow_sdk.cli.main %*
endlocal
