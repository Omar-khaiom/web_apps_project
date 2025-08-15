# 📱 SmartRecipes APK Builder

Build a real Android APK from your web app that people can download and install like any other app!

## ✅ Prerequisites

Before building the APK, make sure you have:

1. **Node.js** (v16 or higher) - [Download here](https://nodejs.org)
2. **Java JDK** (v8 or higher) - [Download here](https://adoptium.net/)
3. **Android SDK** - Two options:
   - Install [Android Studio](https://developer.android.com/studio) (easiest)
   - Or install [Android Command Line Tools](https://developer.android.com/studio/command-line) (smaller)

## 🔧 Setup Android SDK

After installing Android SDK, set the environment variable:

### Windows:
```powershell
# Add to your system environment variables
ANDROID_HOME = C:\Users\YourName\AppData\Local\Android\Sdk
```

### Or set it temporarily in PowerShell:
```powershell
$env:ANDROID_HOME = "C:\Users\YourName\AppData\Local\Android\Sdk"
```

## 🚀 Build Your APK

1. **Open PowerShell in your project folder:**
   ```powershell
   cd D:\web_apps_project
   ```

2. **Run the build script:**
   ```powershell
   .\build-apk.ps1
   ```
   
   If you get an execution policy error, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\build-apk.ps1
   ```

3. **The script will:**
   - Check all prerequisites
   - Install Cordova and dependencies
   - Detect your local IP address
   - Build the APK file
   - Show you where to find it

## 📁 APK Location

Your APK will be created at:
```
platforms\android\app\build\outputs\apk\debug\app-debug.apk
```

## 📲 Install on Android

1. **Enable Unknown Sources:**
   - Go to Android Settings
   - Search for "Install unknown apps"
   - Enable it for your file manager

2. **Transfer the APK:**
   - Copy the `.apk` file to your Android device
   - Use USB, email, or cloud storage

3. **Install the APK:**
   - Open the APK file on your Android device
   - Tap "Install"

## 🌐 Running the Server for APK

Your APK needs to connect to your Flask server. Run it with network access:

```powershell
python app.py --network
```

Make sure your Android device is on the same WiFi network as your computer!

## 🔥 What This APK Does

✅ **Real Native App Experience:**
- Appears in app drawer with your icon
- Works offline (cached content)
- No browser address bar
- Full-screen experience
- Native Android back button support

✅ **Smart Server Detection:**
- Automatically finds your Flask server
- Tests multiple connection methods  
- Shows connection status
- Retry functionality

✅ **Professional Features:**
- Splash screen with your branding
- Network status monitoring
- Error handling and recovery
- Proper Android permissions

## 🐛 Troubleshooting

**"Node.js not found"**
- Download and install Node.js from https://nodejs.org

**"Java not found"**
- Install Java JDK from https://adoptium.net/

**"ANDROID_HOME not set"**
- Install Android Studio or Command Line Tools
- Set the environment variable to your SDK path

**"APK won't install"**
- Enable "Unknown Sources" in Android settings
- Make sure the APK file isn't corrupted

**"App can't connect to server"**
- Run Flask with: `python app.py --network`
- Make sure both devices are on same WiFi
- Check your firewall settings

## 🎯 Next Steps

Once you have a working APK:

1. **For Distribution:**
   - Build a release APK: Answer "y" when the script asks
   - Sign the APK for Google Play Store
   - Create proper app store assets

2. **For Development:**
   - Test on different Android devices
   - Add more native features using Cordova plugins
   - Deploy your Flask server to the cloud

## 💡 Tips

- The APK is about 3-5 MB in size
- It works on Android 7.0+ (API level 24+)
- Users can install it like any other app
- No "it's just a website" feeling - it's a real app!

---

**🎉 Congratulations!** You've turned your web app into a real Android app that users can download and install from anywhere - no app stores required!
