# 🔄 How to Build & Update APK - Complete Guide

**📱 SmartRecipes App - APK Build & Update Process**

This is your complete guide for creating new APK versions whenever you make changes to your SmartRecipes app.

---

## 🎯 **Quick Reference - When Do You Need a New APK?**

### ✅ **NEED New APK For:**
- ✏️ **App content changes** (HTML, CSS, JavaScript modifications)
- 🎨 **Icon changes** (new app icon designs)
- ⚙️ **Configuration updates** (app name, settings)
- 🔗 **Server URL changes** (ngrok URLs, API endpoints)
- 📱 **New features** (additional functionality)

### ❌ **DON'T NEED New APK For:**
- 🐍 **Server-side changes** (Flask `app.py` modifications)
- 🗄️ **Database updates** (recipe content, user data)
- 📊 **Data-only changes** (no UI/functionality changes)

---

## 🚀 **Method 1: Quick Update (Recommended)**

**Use this when you made small changes and want to update quickly.**

### **Step 1: Make Your Changes**
```powershell
# Edit any of these files as needed:
# - index.html (main app)
# - static/css/ (styles)  
# - static/js/ (functionality)
# - static/icons/ (app icons)
```

### **Step 2: Run the Build Script**
```powershell
# Navigate to your project (if not already there)
cd "D:\web_apps_project"

# Run the automated build script
.\build-apk.bat
```

### **Step 3: Complete the Build**
```powershell
# If the script stops after Capacitor sync, continue manually:
cd android
.\gradlew assembleDebug
cd ..
```

### **Step 4: Create New Version**
```powershell
# Copy the built APK with a new version number
Copy-Item "android\app\build\outputs\apk\debug\app-debug.apk" -Destination "SmartRecipes-v1.X-debug.apk"

# Replace X with next version number (e.g., v1.2, v1.3, etc.)
```

### **✅ Done!** Your new APK is ready at `SmartRecipes-v1.X-debug.apk`

---

## 🔧 **Method 2: Clean Build (For Major Changes)**

**Use this when you made significant changes or want to ensure a completely fresh build.**

### **Step 1: Clean Previous Build**
```powershell
# Navigate to project
cd "D:\web_apps_project"

# Remove old web assets
Remove-Item "www\static" -Recurse -Force -ErrorAction SilentlyContinue

# Optional: Clean Android build cache
cd android
.\gradlew clean
cd ..
```

### **Step 2: Copy Fresh Assets**
```powershell
# Copy main HTML file
Copy-Item "index.html" "www\" -Force

# Copy all static assets (icons, CSS, JS, images)
xcopy "static" "www\static\" /E /I /Y
```

### **Step 3: Sync Capacitor**
```powershell
# Sync web assets to Android project
npx cap sync android
```

### **Step 4: Build APK**
```powershell
# Build the Android APK
cd android
.\gradlew assembleDebug
cd ..
```

### **Step 5: Create Shareable Version**
```powershell
# Create your distributable APK
Copy-Item "android\app\build\outputs\apk\debug\app-debug.apk" -Destination "SmartRecipes-v1.X-debug.apk"
```

---

## 🎨 **Special Case: Updating App Icons**

**When you want to change the app icon that appears on the phone:**

### **Step 1: Prepare Your New Icon**
- Create a **1024x1024 PNG** image of your new icon
- Use tools like Canva, GIMP, or online icon generators
- Save it as `new-icon.png` in your project folder

### **Step 2: Generate All Icon Sizes**
**Option A: Use Online Tool (Recommended)**
1. Go to **AppIcon.co** or **IconKitchen**
2. Upload your 1024x1024 image
3. Download all generated sizes
4. Replace files in `static\icons\` folder:
   - `icon-72x72.png`
   - `icon-96x96.png`
   - `icon-128x128.png`
   - `icon-144x144.png`
   - `icon-152x152.png`
   - `icon-192x192.png`
   - `icon-384x384.png`
   - `icon-512x512.png`

### **Step 3: Update Android Launcher Icons**
```powershell
# Copy icons to Android launcher folders
cd "static\icons"

# Update all density folders
Copy-Item "48.png" -Destination "..\..\android\app\src\main\res\mipmap-mdpi\ic_launcher.png" -Force
Copy-Item "icon-72x72.png" -Destination "..\..\android\app\src\main\res\mipmap-hdpi\ic_launcher.png" -Force
Copy-Item "icon-96x96.png" -Destination "..\..\android\app\src\main\res\mipmap-xhdpi\ic_launcher.png" -Force
Copy-Item "icon-144x144.png" -Destination "..\..\android\app\src\main\res\mipmap-xxhdpi\ic_launcher.png" -Force
Copy-Item "icon-192x192.png" -Destination "..\..\android\app\src\main\res\mipmap-xxxhdpi\ic_launcher.png" -Force

# Also update round icons
Copy-Item "48.png" -Destination "..\..\android\app\src\main\res\mipmap-mdpi\ic_launcher_round.png" -Force
Copy-Item "icon-72x72.png" -Destination "..\..\android\app\src\main\res\mipmap-hdpi\ic_launcher_round.png" -Force
Copy-Item "icon-96x96.png" -Destination "..\..\android\app\src\main\res\mipmap-xhdpi\ic_launcher_round.png" -Force
Copy-Item "icon-144x144.png" -Destination "..\..\android\app\src\main\res\mipmap-xxhdpi\ic_launcher_round.png" -Force
Copy-Item "icon-192x192.png" -Destination "..\..\android\app\src\main\res\mipmap-xxxhdpi\ic_launcher_round.png" -Force

# IMPORTANT: Also update adaptive icon foregrounds (for modern Android)
Copy-Item "48.png" -Destination "..\..\android\app\src\main\res\mipmap-mdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-72x72.png" -Destination "..\..\android\app\src\main\res\mipmap-hdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-96x96.png" -Destination "..\..\android\app\src\main\res\mipmap-xhdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-144x144.png" -Destination "..\..\android\app\src\main\res\mipmap-xxhdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-192x192.png" -Destination "..\..\android\app\src\main\res\mipmap-xxxhdpi\ic_launcher_foreground.png" -Force

cd ..\..
```

### **Step 4: Build APK with New Icons**
```powershell
# Use Method 1 or Method 2 above to build APK
.\build-apk.bat
# ... continue with build process
```

---

## 🔍 **Troubleshooting Common Issues**

### **Problem: Build Script Stops After Capacitor Sync**
**Solution:**
```powershell
# Continue manually:
cd android
.\gradlew assembleDebug
cd ..
```

### **Problem: "Cannot find gradlew" Error**
**Solution:**
```powershell
# Make sure you're in the android folder:
cd "D:\web_apps_project\android"
.\gradlew assembleDebug
```

### **Problem: APK Not Updating with Changes**
**Solution:**
```powershell
# Do a clean build:
Remove-Item "www\static" -Recurse -Force
# Then rebuild following Method 2
```

### **Problem: Icons Not Showing in APK**
**Solution:**
```powershell
# Check icon files exist:
ls "static\icons\icon-*.png"
# If missing, recreate them from Method 2 in Icon section
```

### **Problem: APK Size Too Large**
**Solution:**
```powershell
# Remove unnecessary files before building:
# - Large unused images in static\images\
# - Backup files or duplicates
# - Old APK versions (keep latest 2-3 versions)
```

### **Problem: APK Shows White Background with Blue "T" Icons**
**This is the default Capacitor adaptive icon - your custom icons aren't being applied!**
**Solution:**
```powershell
# Update adaptive icon foregrounds (modern Android uses these instead of regular icons)
cd "static\icons"
Copy-Item "48.png" -Destination "..\..\android\app\src\main\res\mipmap-mdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-72x72.png" -Destination "..\..\android\app\src\main\res\mipmap-hdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-96x96.png" -Destination "..\..\android\app\src\main\res\mipmap-xhdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-144x144.png" -Destination "..\..\android\app\src\main\res\mipmap-xxhdpi\ic_launcher_foreground.png" -Force
Copy-Item "icon-192x192.png" -Destination "..\..\android\app\src\main\res\mipmap-xxxhdpi\ic_launcher_foreground.png" -Force
cd ..\..

# Then rebuild APK
cd android; .\gradlew assembleDebug; cd ..
```

---

## 📋 **Version Management System**

### **Naming Convention:**
- `SmartRecipes-v1.0-debug.apk` ← Initial version
- `SmartRecipes-v1.1-debug.apk` ← Minor updates (icon change)
- `SmartRecipes-v1.2-debug.apk` ← Feature additions
- `SmartRecipes-v2.0-debug.apk` ← Major updates

### **When to Increment Version:**
- **0.1 increment:** Small changes (bug fixes, icon updates)
- **1.0 increment:** New features, significant changes
- **Major increment:** Complete rewrites or major functionality changes

### **Keep Track of Changes:**
```powershell
# Create a simple log file
echo "v1.1 - Updated app icons, fixed icon sync issue" >> version-log.txt
echo "v1.2 - Added new recipe categories" >> version-log.txt
```

---

## 📱 **Testing Your New APK**

### **Quick Test Checklist:**
1. **✅ APK file created** (check timestamp is recent)
2. **✅ File size reasonable** (around 30-35 MB for SmartRecipes)
3. **✅ Install on Android device** (enable "Install unknown apps")
4. **✅ App launches correctly**
5. **✅ Icon appears as expected**
6. **✅ Main features work**
7. **✅ Server connection works** (if using Flask backend)

### **Installation Commands:**
```powershell
# Check APK details
Get-ItemProperty "SmartRecipes-v1.X-debug.apk" | Select-Object Name, LastWriteTime, Length

# Share APK (copy to USB, email, etc.)
Copy-Item "SmartRecipes-v1.X-debug.apk" -Destination "C:\Users\$env:USERNAME\Desktop\"
```

---

## 🎯 **Quick Commands Cheat Sheet**

```powershell
# Quick rebuild (most common)
cd "D:\web_apps_project"
.\build-apk.bat
cd android; .\gradlew assembleDebug; cd ..
Copy-Item "android\app\build\outputs\apk\debug\app-debug.apk" -Destination "SmartRecipes-v1.X-debug.apk"

# Clean rebuild (for major changes)
Remove-Item "www\static" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "index.html" "www\" -Force
xcopy "static" "www\static\" /E /I /Y
npx cap sync android
cd android; .\gradlew assembleDebug; cd ..
Copy-Item "android\app\build\outputs\apk\debug\app-debug.apk" -Destination "SmartRecipes-v1.X-debug.apk"

# Check what you have
ls *.apk
ls "static\icons\icon-*.png"
Get-ItemProperty "SmartRecipes-v1.X-debug.apk" | Select-Object Name, LastWriteTime, Length
```

---

## 📂 **File Structure Reference**

```
D:\web_apps_project\
├── 📱 SmartRecipes-v1.X-debug.apk    ← Your shareable APK
├── 📄 index.html                      ← Main app file  
├── 📁 static\
│   ├── 🎨 icons\                      ← App icons (icon-XXXxXXX.png)
│   ├── 🖼️ images\                     ← App images
│   ├── 💅 css\                        ← Stylesheets
│   └── ⚡ js\                         ← JavaScript
├── 📁 android\                        ← Android build system
│   └── 📁 app\build\outputs\apk\debug\
│       └── 📱 app-debug.apk           ← Build output
├── 📁 www\                            ← Capacitor web directory
├── 🔧 build-apk.bat                   ← Your build script
└── 📚 APK_MANAGEMENT_GUIDE.md         ← Detailed guide
```

---

## 🎉 **Summary**

**For most updates:** Use Method 1 (Quick Update)  
**For icon changes:** Follow the Special Case guide  
**For major changes:** Use Method 2 (Clean Build)

**Remember:** Always increment your version number and test the APK before sharing!

---

**💡 Pro Tip:** Keep the last 2-3 APK versions in case you need to rollback. Delete older versions to save space.

**🤝 Need Help?** Check the existing `APK_MANAGEMENT_GUIDE.md` for more detailed information.

---

*Last Updated: August 2025*  
*APK Build System: Capacitor + Android Gradle*
