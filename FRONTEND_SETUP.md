# 🚀 Frontend Setup Guide

## Quick Start - Run These Commands One by One

### Step 1: Open Terminal
Open PowerShell or Command Prompt in the `Stock Market` folder.

### Step 2: Activate Virtual Environment (if using one)
```bash
# If you have a virtual environment, activate it first:
venv\Scripts\activate
```

### Step 3: Install/Verify Dependencies
```bash
# Make sure Flask is installed:
pip install flask uvicorn
```

### Step 4: Start the Server
```bash
python app.py
```

**Expected Output:**
```
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO: Application startup complete.
```

### Step 5: Open Browser
Open your web browser and navigate to:
```
http://localhost:8000
```

### Step 6: View the Dashboard
You should see:
- ✅ Circular AI Score Gauges (1-10 scale with color coding)
- ✅ Stock prediction cards with ratings (Strong Buy/Buy/Hold/Sell/Strong Sell)
- ✅ Probability bars showing confidence
- ✅ Market context header (S&P 500, Oil, Market Regime)
- ✅ Premium dark theme with glassmorphism effects

---

## 🔄 If You Need to Refresh

### Hard Refresh (Recommended)
Press **Ctrl + Shift + R** (Windows/Linux) or **Cmd + Shift + R** (Mac)

This clears the browser cache and loads the latest version.

---

## 🛑 To Stop the Server

Press **Ctrl + C** in the terminal where `app.py` is running.

---

## 📂 Frontend Files

The Danelfin-inspired design includes:
- `static/script.js` - Main dashboard logic with circular gauges
- `static/danelfin_ui.js` - Circular gauge generator functions
- `static/danelfin_styles.css` - Premium styling (glassmorphism, gradients)
- `static/style.css` - Base dark theme styles
- `static/index.html` - Main HTML template

---

## 🐛 Troubleshooting

### Server won't start
**Issue:** Port 8000 is already in use
**Solution:**
```bash
# Find the process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with the actual process ID)
taskkill /PID <PID> /F

# Then restart: python app.py
```

### Circular gauges not showing
**Issue:** Browser cache is showing old version
**Solution:** Hard refresh with **Ctrl + Shift + R**

### JavaScript errors in console
**Issue:** Old cached JavaScript files
**Solution:**
1. Hard refresh: **Ctrl + Shift + R**
2. Clear browser cache completely
3. Close and reopen browser

---

## ✅ What You Should See

### Dashboard Features:
1. **Circular AI Score Gauge** - Beautiful circular progress ring showing 1-10 confidence
2. **Color-Coded Ratings:**
   - 🔴 Red (1-2): Strong Sell
   - 🟠 Orange (3-4): Sell  
   - 🟡 Yellow (5-6): Hold
   - 🟢 Light Green (7-8): Buy
   - 🟢 Dark Green (9-10): Strong Buy
3. **Probability Bars** - Sliding indicator showing prediction probability
4. **Multi-Timeframe Predictions** - Weekly outlook + Daily prediction
5. **Market Context** - S&P 500, Crude Oil, Market Regime in header
6. **Premium Design** - Glassmorphism effects, gradient borders, smooth animations

---

## 📱 Access from Other Devices

To access from another computer/phone on the same network:

1. Find your computer's IP address:
   ```bash
   ipconfig
   # Look for IPv4 Address (e.g., 192.168.1.100)
   ```

2. On the other device, navigate to:
   ```
   http://YOUR_IP_ADDRESS:8000
   ```

---

## 🎯 First Time Setup Complete!

Your institutional-grade AI stock prediction dashboard is now running! 🚀

Enjoy the premium Danelfin-inspired design with circular gauges and probabilistic predictions! 📈💎
