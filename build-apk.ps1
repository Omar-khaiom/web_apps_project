# 📱 SmartRecipes APK Builder Script
# This script creates a real Android APK from your Flask web app

param(
    [switch]$Release,
    [string]$AppName = "SmartRecipes",
    [string]$PackageName = "com.smartrecipes.app",
    [string]$Version = "1.0.0"
)

# Colors for console output
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️ $Message" "Yellow" }
function Write-Info { param([string]$Message) Write-ColorOutput "ℹ️ $Message" "Cyan" }

# Header
Write-ColorOutput "`n🚀 SmartRecipes APK Builder" "Magenta"
Write-ColorOutput "================================`n" "Magenta"

# Check prerequisites
Write-Info "Checking prerequisites..."

# Check Node.js
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Success "Node.js found: $nodeVersion"
    } else {
        Write-Error "Node.js not found. Please install Node.js from https://nodejs.org"
        exit 1
    }
} catch {
    Write-Error "Node.js not found. Please install Node.js from https://nodejs.org"
    exit 1
}

# Check Java
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    if ($javaVersion) {
        Write-Success "Java found: $($javaVersion.Line)"
    } else {
        Write-Error "Java not found. Please install Java JDK from https://adoptium.net/"
        exit 1
    }
} catch {
    Write-Error "Java not found. Please install Java JDK from https://adoptium.net/"
    exit 1
}

# Check Android SDK
if (-not $env:ANDROID_HOME) {
    Write-Warning "ANDROID_HOME environment variable not set."
    Write-Info "Trying to detect Android SDK automatically..."
    
    $possiblePaths = @(
        "$env:USERPROFILE\AppData\Local\Android\Sdk",
        "$env:LOCALAPPDATA\Android\Sdk",
        "C:\Android\Sdk",
        "${env:ProgramFiles(x86)}\Android\android-sdk"
    )
    
    $foundSdk = $false
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $env:ANDROID_HOME = $path
            Write-Success "Android SDK found at: $path"
            $foundSdk = $true
            break
        }
    }
    
    if (-not $foundSdk) {
        Write-Error "Android SDK not found. Please install Android Studio or Android Command Line Tools."
        Write-Info "Download from: https://developer.android.com/studio"
        exit 1
    }
} else {
    Write-Success "Android SDK found: $env:ANDROID_HOME"
}

# Get local IP address
Write-Info "Detecting local IP address..."
$localIP = ""
try {
    $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
        $_.InterfaceAlias -like "*Wi-Fi*" -or 
        $_.InterfaceAlias -like "*Ethernet*" -or
        $_.InterfaceAlias -like "*Wireless*"
    } | Where-Object { 
        $_.IPAddress -match "^192\." -or 
        $_.IPAddress -match "^10\." -or 
        $_.IPAddress -match "^172\."
    } | Sort-Object InterfaceAlias | Select-Object -First 1
    
    if ($networkAdapters) {
        $localIP = $networkAdapters.IPAddress
        Write-Success "Local IP detected: $localIP"
    } else {
        $localIP = "localhost"
        Write-Warning "Could not detect local IP, using localhost"
    }
} catch {
    $localIP = "localhost"
    Write-Warning "Could not detect local IP, using localhost"
}

# Install Cordova if not present
Write-Info "Checking Cordova installation..."
try {
    $cordovaVersion = cordova --version 2>$null
    if ($cordovaVersion) {
        Write-Success "Cordova found: $cordovaVersion"
    } else {
        Write-Info "Installing Cordova..."
        npm install -g cordova
        Write-Success "Cordova installed successfully"
    }
} catch {
    Write-Info "Installing Cordova..."
    npm install -g cordova
    Write-Success "Cordova installed successfully"
}

# Create Cordova project if it doesn't exist
if (-not (Test-Path "config.xml")) {
    Write-Info "Creating Cordova project..."
    cordova create . $PackageName $AppName
    
    # Remove default www folder and create our own
    if (Test-Path "www") {
        Remove-Item -Recurse -Force "www"
    }
    New-Item -ItemType Directory -Force -Path "www" | Out-Null
} else {
    Write-Success "Cordova project already exists"
}

# Create www/index.html
Write-Info "Creating app HTML structure..."

# Create the HTML content as a file directly to avoid PowerShell parsing issues
$htmlContent = @"
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>$AppName</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .splash { 
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            color: white; z-index: 9999;
        }
        .logo { font-size: 3rem; margin-bottom: 1rem; }
        .spinner { border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; 
                  border-top: 3px solid white; width: 40px; height: 40px; 
                  animation: spin 1s linear infinite; margin: 1rem 0; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .status { margin-top: 1rem; font-size: 0.9rem; opacity: 0.9; text-align: center; }
        .app-frame { width: 100%; height: 100vh; border: none; display: none; }
        .error-screen { display: none; padding: 2rem; text-align: center; }
        .retry-btn { 
            background: #4CAF50; color: white; border: none; padding: 12px 24px;
            border-radius: 5px; font-size: 1rem; margin-top: 1rem; cursor: pointer;
        }
    </style>
</head>
<body>
    <div id="splash" class="splash">
        <div class="logo">🍳</div>
        <h1>$AppName</h1>
        <div class="spinner"></div>
        <div id="status" class="status">Connecting to server...</div>
    </div>
    
    <div id="error-screen" class="error-screen">
        <h2>Connection Failed</h2>
        <p id="error-message">Unable to connect to the server</p>
        <button id="retry-btn" class="retry-btn" onclick="connectToServer()">Retry Connection</button>
    </div>
    
    <iframe id="app-frame" class="app-frame" src="about:blank"></iframe>
    
    <script>
        let serverUrls = [
            'http://$localIP:5000',
            'http://localhost:5000',
            'http://127.0.0.1:5000',
            'http://192.168.1.100:5000',
            'http://10.0.0.100:5000'
        ];
        
        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }
        
        function showError(message) {
            document.getElementById('splash').style.display = 'none';
            document.getElementById('error-screen').style.display = 'block';
            document.getElementById('error-message').textContent = message;
        }
        
        function showApp(url) {
            const frame = document.getElementById('app-frame');
            frame.src = url;
            frame.onload = function() {
                document.getElementById('splash').style.display = 'none';
                frame.style.display = 'block';
            };
        }
        
        async function testServer(url) {
            try {
                updateStatus('Trying ' + url + '...');
                const response = await fetch(url, { 
                    method: 'GET',
                    mode: 'no-cors',
                    timeout: 5000 
                });
                return true;
            } catch (error) {
                return false;
            }
        }
        
        async function connectToServer() {
            document.getElementById('error-screen').style.display = 'none';
            document.getElementById('splash').style.display = 'flex';
            
            for (let i = 0; i < serverUrls.length; i++) {
                const url = serverUrls[i];
                const isReachable = await testServer(url);
                
                if (isReachable) {
                    updateStatus('Connected! Loading app...');
                    showApp(url);
                    return;
                }
            }
            
            showError('Could not connect to any server. Make sure your Flask app is running with --network flag.');
        }
        
        document.addEventListener('deviceready', connectToServer, false);
        
        if (!window.cordova) {
            setTimeout(connectToServer, 1000);
        }
    </script>
    
    <script src="cordova.js"></script>
</body>
</html>
"@

$htmlContent | Out-File -FilePath "www/index.html" -Encoding UTF8

# Add Android platform if not exists
Write-Info "Adding Android platform..."
try {
    cordova platform ls | Out-String | ForEach-Object {
        if ($_ -notmatch "android") {
            cordova platform add android
            Write-Success "Android platform added"
        } else {
            Write-Success "Android platform already exists"
        }
    }
} catch {
    cordova platform add android
    Write-Success "Android platform added"
}

# Install required plugins
Write-Info "Installing Cordova plugins..."
$plugins = @(
    "cordova-plugin-whitelist",
    "cordova-plugin-network-information",
    "cordova-plugin-splashscreen"
)

foreach ($plugin in $plugins) {
    try {
        cordova plugin ls | Out-String | ForEach-Object {
            if ($_ -notmatch $plugin) {
                cordova plugin add $plugin
                Write-Success "Plugin $plugin installed"
            }
        }
    } catch {
        cordova plugin add $plugin
        Write-Success "Plugin $plugin installed"
    }
}

# Update config.xml
Write-Info "Updating app configuration..."
$configContent = @"
<?xml version='1.0' encoding='utf-8'?>
<widget id="$PackageName" version="$Version" xmlns="http://www.w3.org/ns/widgets" xmlns:cdv="http://cordova.apache.org/ns/1.0">
    <name>$AppName</name>
    <description>Smart recipe discovery app</description>
    <author email="your-email@example.com">Your Name</author>
    <content src="index.html" />
    
    <allow-intent href="http://*/*" />
    <allow-intent href="https://*/*" />
    <allow-intent href="tel:*" />
    <allow-intent href="sms:*" />
    <allow-intent href="mailto:*" />
    <allow-intent href="geo:*" />
    
    <platform name="android">
        <allow-intent href="market:*" />
        <preference name="Orientation" value="portrait" />
        <preference name="SplashMaintainAspectRatio" value="true" />
        <preference name="SplashShowOnlyFirstTime" value="false" />
        <preference name="SplashScreen" value="screen" />
        <preference name="SplashScreenDelay" value="3000" />
        <icon density="ldpi" src="www/res/icon/android/ldpi.png" />
        <icon density="mdpi" src="www/res/icon/android/mdpi.png" />
        <icon density="hdpi" src="www/res/icon/android/hdpi.png" />
        <icon density="xhdpi" src="www/res/icon/android/xhdpi.png" />
        <icon density="xxhdpi" src="www/res/icon/android/xxhdpi.png" />
        <icon density="xxxhdpi" src="www/res/icon/android/xxxhdpi.png" />
    </platform>
    
    <plugin name="cordova-plugin-whitelist" spec="^1.3.5" />
    <plugin name="cordova-plugin-network-information" spec="^3.0.0" />
    <plugin name="cordova-plugin-splashscreen" spec="^6.0.2" />
    
    <access origin="*" />
    <allow-navigation href="http://*/*" />
    <allow-navigation href="https://*/*" />
</widget>
"@

$configContent | Out-File -FilePath "config.xml" -Encoding UTF8

# Build the APK
Write-Info "Building APK..."
if ($Release) {
    Write-Info "Building release APK..."
    cordova build android --release
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Release APK built successfully!"
        $apkPath = "platforms\android\app\build\outputs\apk\release\app-release-unsigned.apk"
        if (Test-Path $apkPath) {
            Write-Success "APK location: $apkPath"
            Write-Warning "Note: Release APK needs to be signed before distribution"
        }
    } else {
        Write-Error "Failed to build release APK"
        exit 1
    }
} else {
    Write-Info "Building debug APK..."
    cordova build android
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Debug APK built successfully!"
        $apkPath = "platforms\android\app\build\outputs\apk\debug\app-debug.apk"
        if (Test-Path $apkPath) {
            $apkSize = [math]::Round((Get-Item $apkPath).Length / 1MB, 2)
            Write-Success "APK location: $apkPath"
            Write-Success "APK size: ${apkSize} MB"
            
            # Instructions
            Write-ColorOutput "`n🎉 APK Build Complete!" "Green"
            Write-ColorOutput "===================" "Green"
            Write-Info "1. Transfer the APK to your Android device"
            Write-Info "2. Enable 'Install from unknown sources' in Android settings"
            Write-Info "3. Install the APK"
            Write-Info "4. Run your Flask server with: python app.py --network"
            Write-Info "5. Make sure both devices are on the same WiFi network"
            Write-ColorOutput "`n📱 Server IP for APK: $localIP:5000" "Yellow"
        }
    } else {
        Write-Error "Failed to build debug APK"
        exit 1
    }
}

Write-ColorOutput "`n✨ Build process completed!" "Magenta"