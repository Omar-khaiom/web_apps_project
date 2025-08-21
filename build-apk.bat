@echo off
echo Building SmartRecipes APK...
echo.

echo Step 1: Setting Android SDK environment
set ANDROID_HOME=C:\Users\%USERNAME%\AppData\Local\Android\Sdk
echo Android SDK: %ANDROID_HOME%
echo.

echo Step 2: Copying web assets to www folder
copy index.html www\ /Y
xcopy static www\static\ /E /I /Y
echo.

echo Step 3: Syncing Capacitor
npx cap sync android
echo.

echo Step 4: Building Debug APK
cd android
.\gradlew assembleDebug
echo.

echo Step 5: Building Release APK
.\gradlew assembleRelease
echo.

echo Step 6: APK Locations
echo Debug APK: android\app\build\outputs\apk\debug\app-debug.apk
echo Release APK: android\app\build\outputs\apk\release\app-release-unsigned.apk
echo.
echo Build completed successfully!
echo.

pause
