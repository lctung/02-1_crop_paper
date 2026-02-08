@echo off
setlocal enabledelayedexpansion
set "POPPLER_BIN=C:\Users\ctl20\.conda\envs\fontenv\Library\bin\pdftoppm.exe"

for %%f in (*.pdf) do (
    echo [*] Processing... %%f

    :: 抓取檔名並建立資料夾
    set "outdir=rotated_%%~nf"
    mkdir "!outdir!" 2>nul
    
    :: 執行轉換
    "!POPPLER_BIN!" -png -r 300 "%%f" "!outdir!\"
)

echo.
echo === 全部 PDF 處理完畢 ===
pause