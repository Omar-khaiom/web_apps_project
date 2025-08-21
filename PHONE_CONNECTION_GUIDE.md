# 📱 SmartRecipes Phone App Connection Guide

## ✅ Quick Fix Steps

### Step 1: Make Sure Server is Running
```bash
# Run this command on your PC:
python app.py --network
```
**You should see:**
- ✅ `🌐 Running with network access enabled`
- ✅ `📱 Your APK can now connect to this server`
- ✅ `Running on http://192.168.0.100:5000`

### Step 2: Check WiFi Connection
- ✅ **PC and Phone must be on the SAME WiFi network**
- ✅ Your PC IP: `192.168.0.100`
- ✅ Test on PC: Open browser → `http://192.168.0.100:5000`

### Step 3: Install Latest APK
- ✅ **Use: SmartRecipes-v1.7-debug.apk** (prioritizes local network)
- ✅ Upload to Google Drive → Download on phone → Install

---

## 🔧 If Still Not Working

### Test 1: Browser Test on Phone
1. Open your **phone's browser**
2. Go to: `http://192.168.0.100:5000`
3. ✅ **Should show SmartRecipes web app**
4. ❌ **If doesn't work**: WiFi connection issue

### Test 2: PC Firewall Check
```bash
# Run on PC to temporarily disable firewall for testing:
netsh advfirewall set allprofiles state off

# After testing, re-enable:
netsh advfirewall set allprofiles state on
```

### Test 3: Check Windows Firewall
- Windows Settings → Update & Security → Windows Security
- Firewall & network protection → Allow an app through firewall
- Add Python.exe if not listed

---

## 🌐 Alternative: Ngrok Method

If local network doesn't work, use ngrok:

### Step 1: Fix Ngrok Warning
1. Open phone browser first
2. Go to: `https://seriously-ready-kid.ngrok-free.app`
3. Click "Visit Site" when you see warning
4. Then launch the app

### Step 2: Use Ngrok APK
- The v1.7 APK tries local network first, then ngrok as backup

---

## 📋 Connection Priority Order

The app tries these URLs in order:
1. **`http://192.168.0.100:5000`** (Local network - fastest)
2. **`https://seriously-ready-kid.ngrok-free.app`** (Ngrok tunnel - backup)
3. **`http://localhost:5000`** (Browser testing only)
4. **`http://127.0.0.1:5000`** (Final fallback)

---

## 🚨 Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| "Connection failed retrying" | Check if both PC and phone on same WiFi |
| "Unable to connect" | Make sure Flask server is running with `--network` |
| Ngrok warning page | Open in phone browser first, click "Visit Site" |
| App crashes | Try reinstalling APK, enable USB debugging |
| Server not found | Check PC firewall settings |

---

## 📞 Debug Commands

### On PC:
```bash
# Check server status
python app.py --network

# Check IP address
ipconfig | findstr "IPv4"

# Test local connection
curl http://192.168.0.100:5000

# Check if port is open
netstat -an | findstr 5000
```

### On Phone:
- Install APK: **SmartRecipes-v1.7-debug.apk**
- Enable Developer Options → USB Debugging (for logging)
- If using ADB: `adb logcat | findstr "SmartRecipes"`

---

## ✅ Success Indicators

You'll know it's working when:
- App shows "Connected! Loading app..." 
- Web interface loads in the app
- No more "connection failed retrying" messages

**🎯 The v1.7 APK should work with local network connection!**
