@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
rem Admin kerak emas. Talab: Python 3.11+ (64-bit), Inno Setup 6.3+
if not exist "requirements.txt" (
  echo Loyiha fayllari topilmadi: %CD%
  echo Zip ichidan ishga tushirmang. Avval zip ustida o'ng tugma - "Izvlech vse / Extract All",
  echo keyin ochilgan papkadagi build.bat ni ishga tushiring.
  goto :err
)

echo [1/4] Kutubxonalar o'rnatilmoqda...
python -m pip install --user -q -r requirements.txt pyinstaller || goto :err

echo [2/4] Dastur yig'ilmoqda...
python -m PyInstaller --noconfirm --clean --onedir --noconsole --collect-all vosk --icon assets\ovozyoz.ico --name OvozYoz main.py || goto :err

echo [3/4] O'zbekcha model...
if not exist models mkdir models
if exist "models\vosk-model-small-uz-0.22\am" goto :model_ok
if exist "models\vosk-model-small-uz-0.22.zip" goto :model_unzip
rem Asosiy sayt ishlamasa - Hugging Face nusxasidan yuklaydi
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; $u=@('https://alphacephei.com/vosk/models/vosk-model-small-uz-0.22.zip','https://huggingface.co/rhasspy/vosk-models/resolve/main/uz/vosk-model-small-uz-0.22.zip'); foreach($x in $u){ try { Write-Host ('Yuklanmoqda: '+$x); Invoke-WebRequest -Uri $x -OutFile 'models\vosk-model-small-uz-0.22.zip'; exit 0 } catch { Write-Host ('  ishlamadi: '+$_.Exception.Message); Remove-Item 'models\vosk-model-small-uz-0.22.zip' -ErrorAction SilentlyContinue } }; exit 1" || goto :model_manual
:model_unzip
powershell -NoProfile -Command "Expand-Archive -Force 'models\vosk-model-small-uz-0.22.zip' 'models'" || goto :err
if exist "models\vosk-model-small-uz-0.22\am" goto :model_ok
echo Zip ochildi, lekin models\vosk-model-small-uz-0.22\am topilmadi.
goto :err
:model_manual
echo.
echo Model internetdan yuklanmadi. Brauzer orqali yuklab oling:
echo   https://huggingface.co/rhasspy/vosk-models/resolve/main/uz/vosk-model-small-uz-0.22.zip
echo Faylni shu papkaga qo'ying (ochmasdan): %CD%\models
echo va build.bat ni qayta ishga tushiring.
goto :err
:model_ok

echo [4/4] O'rnatuvchi yaratilmoqda...
for /f %%v in ('python -c "import ovozyoz; print(ovozyoz.VERSION)"') do set VER=%%v
set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" for /f "delims=" %%i in ('where ISCC.exe 2^>nul') do set "ISCC=%%i"
if not exist "%ISCC%" (
  echo Inno Setup 6 topilmadi. Yuklab oling: https://jrsoftware.org/isdl.php
  echo O'rnatishda "Install for me only" ni tanlang, keyin build.bat ni qayta ishga tushiring.
  goto :err
)
"%ISCC%" /Q /DAppVersion=%VER% installer\OvozYoz.iss || goto :err

echo.
echo Tayyor: Output\OvozYoz-Setup-%VER%.exe
pause
exit /b 0

:err
echo.
echo XATO. Yuqoridagi xabarni yuboring.
pause
exit /b 1
