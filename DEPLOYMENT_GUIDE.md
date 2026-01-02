# AWS EC2 Deployment Guide for "The Researcher"

This guide outlines the steps to deploy your Stock Analysis System to an AWS EC2 instance.

## Prerequisites
- An AWS Account (Free Tier is fine).
- A domain name (optional, but recommended)
- SSH access to your EC2 instance (Key Pair `.pem` file)
- Your Gemini API Key

## Step 1: Launch an EC2 Instance
1.  **Login** to AWS Console → **EC2** → **Launch Instance**.
2.  **Name**: `The-Researcher-Server`.
3.  **OS Image**: **Ubuntu Server 22.04 LTS** (Free Tier Eligible).
4.  **Instance Type**: `t2.small` or `t3.small` (Recommended for AI - has 2GB RAM).
   - ⚠️ **Note**: `t2.micro` may run out of memory during AI predictions
5.  **Key Pair**: Create a new pair (e.g., `stock-key`), download the `.pem` file.
6.  **Storage**: Increase to **20 GB** (for databases and vector store).
7.  **Network Settings**:
    - Allow SSH traffic from anywhere (0.0.0.0/0).
    - Allow HTTP traffic from the internet.
    - Allow HTTPS traffic from the internet.
8.  **Launch Instance**.

## Step 2: Configure Security Group (Firewall)
1.  Go to **EC2** → **Security Groups**.
2.  Select the one created for your instance.
3.  **Edit Inbound Rules**:
    - **SSH**: Port 22, Source 0.0.0.0/0 (or your IP for security)
    - **HTTP**: Port 80, Source 0.0.0.0/0
    - **Custom TCP**: Port **8000**, Source **0.0.0.0/0** (FastAPI app)

## Step 3: Connect to Server
Use your terminal (Mac/Linux) or PowerShell (Windows).

```bash
# Set permissions for key (Linux/Mac)
chmod 400 stock-key.pem

# For Windows PowerShell, skip chmod and use:
# icacls stock-key.pem /inheritance:r /grant:r "%USERNAME%:R"

# SSH into server (replace x.x.x.x with Public IP from AWS Console)
ssh -i "stock-key.pem" ubuntu@x.x.x.x
```

## Step 4: Server Setup

### 1. Update & Install Python
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

### 2. Clone/Upload Code

**Option A: Git (Recommended)**
```bash
# First, push your code to GitHub (from local machine):
# cd "c:\Stock Market"
# git init
# git add .
# git commit -m "Initial commit"
# git remote add origin https://github.com/yourusername/stock-market.git
# git push -u origin main

# Then on EC2:
git clone https://github.com/yourusername/stock-market.git
cd stock-market
```

**Option B: SCP (Manual Upload)**
Run from your **local** machine (Windows PowerShell):
```powershell
scp -i "stock-key.pem" -r "C:\Stock Market" ubuntu@x.x.x.x:~/stock-market
```

### 3. Install Dependencies
```bash
cd stock-market
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
# Create .env file
nano .env
```

Add your API key:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

## Step 5: Database Handling

Since databases are file-based:
- **If you uploaded files** (Option B): Databases are already there
- **If you git cloned**: Databases will be created automatically on first run

Ensure write permissions:
```bash
chmod -R 755 ~/stock-market
```

## Step 6: Test Run
```bash
# Make sure you're in the venv
source venv/bin/activate

# Run server
python3 app.py
```

**Visit** `http://YOUR_EC2_PUBLIC_IP:8000` in your browser.

You should see:
- Home page at `/`
- Daily predictions at `/daily`
- Weekly at `/weekly`
- Monthly at `/monthly`
- Archive at `/archive`

Press `Ctrl+C` to stop when done testing.

## Step 7: Production Setup (Systemd Service)

To keep it running 24/7:

### 1. Create Service File
```bash
sudo nano /etc/systemd/system/stock-app.service
```

### 2. Paste Content (Update paths and API key):
```ini
[Unit]
Description=The Researcher Stock Prediction API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/stock-market
Environment="GEMINI_API_KEY=your_actual_gemini_api_key_here"
ExecStart=/home/ubuntu/stock-market/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Start & Enable Service
```bash
sudo systemctl daemon-reload
sudo systemctl start stock-app
sudo systemctl enable stock-app

# Check status
sudo systemctl status stock-app

# View logs
sudo journalctl -u stock-app -f
```

## Step 8: Prediction Pipeline (Scheduled Updates)

To automatically update predictions daily at 7 PM:

### 1. Edit Crontab
```bash
crontab -e
```

### 2. Add Scheduled Job
```bash
# Run pipeline daily at 19:00 (7 PM)
0 19 * * * cd /home/ubuntu/stock-market && /home/ubuntu/stock-market/venv/bin/python run_pipeline.py >> /home/ubuntu/stock-market/pipeline.log 2>&1
```

Save and exit (`Ctrl+X`, `Y`, `Enter`).

### 3. Verify Cron
```bash
crontab -l
```

## Step 9: (Optional) Setup Domain & SSL

### Using Nginx as Reverse Proxy

1. **Install Nginx**:
```bash
sudo apt install nginx -y
```

2. **Configure Nginx**:
```bash
sudo nano /etc/nginx/sites-available/stock-app
```

Paste:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /home/ubuntu/stock-market/static;
    }
}
```

3. **Enable Site**:
```bash
sudo ln -s /etc/nginx/sites-available/stock-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. **Setup SSL with Certbot** (Optional but recommended):
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Useful Commands

```bash
# View app logs
sudo journalctl -u stock-app -f

# Restart app
sudo systemctl restart stock-app

# Stop app
sudo systemctl stop stock-app

# Check if app is running
sudo systemctl status stock-app

# Update code from Git
cd ~/stock-market
git pull
sudo systemctl restart stock-app

# View pipeline logs
tail -f ~/stock-market/pipeline.log
```

## Troubleshooting

### App won't start
```bash
# Check logs
sudo journalctl -u stock-app -n 50

# Check if port 8000 is in use
sudo lsof -i :8000

# Test manually
cd ~/stock-market
source venv/bin/activate
python app.py
```

### Out of memory
- Upgrade to `t3.small` instance (2GB RAM)
- Add swap space:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Database permissions
```bash
cd ~/stock-market
sudo chown -R ubuntu:ubuntu .
chmod -R 755 .
```

---

## 🎉 Deployment Complete!

Your application is now live at:
- **Direct**: `http://YOUR_EC2_IP:8000`
- **With Domain**: `http://your-domain.com`

**New Features Deployed:**
- 🏠 Home page with project documentation at `/`
- 📊 Professional UI with glassmorphism design
- 🎯 Confidence level definitions
- 📈 Analytics methodology explanations
- ⏱️ Multiple timeframes (Daily, Weekly, Monthly)
- 📁 Historical archive

**Security Reminders:**
- Change SSH to key-only authentication
- Restrict Security Group rules to specific IPs when possible
- Keep your `.env` file secure
- Never commit API keys to Git
- Regular backup of databases
