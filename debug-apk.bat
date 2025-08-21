@echo off
echo SmartRecipes APK Debugging Tools
echo ================================
echo.

:menu
echo Choose debugging method:
echo 1. Install APK on connected device
echo 2. Start Flask server for app testing
echo 3. Open Chrome DevTools for web debugging
echo 4. View APK contents and info
echo 5. Build debug APK with verbose logging
echo 6. Test APK in browser (simulate mobile)
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto install_device
if "%choice%"=="2" goto start_server
if "%choice%"=="3" goto chrome_debug
if "%choice%"=="4" goto apk_info
if "%choice%"=="5" goto build_debug
if "%choice%"=="6" goto browser_test
if "%choice%"=="7" goto exit
goto menu

:install_device
echo.
echo Installing APK on connected device...
set PATH=%PATH%;C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools
adb devices
echo.
echo If device is listed above, installing APK...
adb install -r android\app\build\outputs\apk\debug\app-debug.apk
echo.
echo Installation complete! Check your device.
pause
goto menu

:start_server
echo.
echo Starting Flask server for app testing...
echo The APK will connect to this server when opened.
echo Keep this window open while testing the APK.
echo.
echo Starting server at http://localhost:5000...
python app.py
pause
goto menu

:chrome_debug
echo.
echo Chrome DevTools Debugging:
echo 1. Connect your Android device via USB
echo 2. Enable USB Debugging on device
echo 3. Install and open SmartRecipes app
echo 4. Open Chrome on PC and go to: chrome://inspect
echo 5. Your app should appear under "Remote Target"
echo 6. Click "Inspect" to debug with DevTools
echo.
start chrome chrome://inspect
pause
goto menu

:apk_info
echo.
echo APK Information:
echo ================
dir android\app\build\outputs\apk\debug\app-debug.apk
echo.
echo APK Contents (if aapt available):
echo Location: android\app\build\outputs\apk\debug\app-debug.apk
echo Size: ~30MB
echo Package: com.smartrecipes.app
echo.
pause
goto menu

:build_debug
echo.
echo Building debug APK with verbose logging...
cd android
.\gradlew assembleDebug --info
echo.
echo Debug build complete with verbose output!
cd ..
pause
goto menu

:browser_test
echo.
echo Testing in browser (mobile simulation)...
echo This opens your web app in Chrome mobile view
echo Use this to test your web app before APK testing
echo.
start chrome --user-agent="Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36" http://localhost:5000
echo.
echo Started Chrome in mobile mode. Make sure Flask server is running!
pause
goto menu

:exit
echo Exiting debug tools...
exit
