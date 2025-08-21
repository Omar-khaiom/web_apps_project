@echo off
echo =========================================
echo   SmartRecipes - Quick APK Update
echo =========================================
echo.

REM Get the next version number from user
set /p VERSION="Enter new version number (e.g., 1.2): "

echo.
echo Building APK version %VERSION%...
echo.

echo Step 1: Running build script
call build-apk.bat

echo.
echo Step 2: Completing Gradle build
cd android
gradlew assembleDebug
cd ..

echo.
echo Step 3: Creating versioned APK
copy "android\app\build\outputs\apk\debug\app-debug.apk" "SmartRecipes-v%VERSION%-debug.apk"

echo.
echo Step 4: Checking APK details
powershell -Command "Get-ItemProperty 'SmartRecipes-v%VERSION%-debug.apk' | Select-Object Name, LastWriteTime, Length"

echo.
echo =========================================
echo   APK Update Complete!
echo   Your new APK: SmartRecipes-v%VERSION%-debug.apk
echo =========================================
echo.
echo Remember to:
echo 1. Test the APK on an Android device
echo 2. Update version-log.txt with your changes
echo 3. Delete old APK versions if needed
echo.

pause
