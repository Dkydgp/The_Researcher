# Quick AWS EC2 Deployment Checklist

## Pre-Deployment
- [ ] Push code to GitHub (or prepare for SCP upload)
- [ ] Have your Gemini API key ready
- [ ] AWS account created and logged in

## EC2 Setup (15 min)
- [ ] Launch Ubuntu 22.04 instance (`t2.small` or `t3.small`)
- [ ] Download `.pem` key file
- [ ] Configure Security Group: Port 22 (SSH), Port 80 (HTTP), Port 8000 (Custom TCP)
- [ ] Note down Public IP address

## Server Configuration (20 min)
```bash
# 1. Connect
ssh -i "stock-key.pem" ubuntu@YOUR_EC2_IP

# 2. Update system
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y

# 3. Get code (choose one)
# Option A - Git:
git clone https://github.com/YOUR_USERNAME/stock-market.git
cd stock-market

# Option B - SCP from local:
# scp -i "stock-key.pem" -r "C:\Stock Market" ubuntu@YOUR_EC2_IP:~/stock-market

# 4. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure API key
nano .env
# Add: GEMINI_API_KEY=your_key_here
# Save: Ctrl+X, Y, Enter

# 6. Test run
python3 app.py
# Visit: http://YOUR_EC2_IP:8000
# Press Ctrl+C to stop
```

## Production Setup (10 min)
```bash
# 1. Create systemd service
sudo nano /etc/systemd/system/stock-app.service
```

Paste (update API key):
```ini
[Unit]
Description=The Researcher Stock Prediction API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/stock-market
Environment="GEMINI_API_KEY=your_actual_key"
ExecStart=/home/ubuntu/stock-market/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Enable and start
sudo systemctl daemon-reload
sudo systemctl start stock-app
sudo systemctl enable stock-app

# 3. Setup daily pipeline (7 PM)
crontab -e
# Add: 0 19 * * * cd /home/ubuntu/stock-market && /home/ubuntu/stock-market/venv/bin/python run_pipeline.py >> pipeline.log 2>&1
```

## Verification
- [ ] Visit `http://YOUR_EC2_IP:8000` - Home page loads
- [ ] Check `/daily`, `/weekly`, `/monthly`, `/archive` pages
- [ ] Run: `sudo systemctl status stock-app` - Shows "active (running)"
- [ ] Check logs: `sudo journalctl -u stock-app -n 20`

## Post-Deployment
- [ ] Bookmark: `http://YOUR_EC2_IP:8000`
- [ ] (Optional) Setup domain name
- [ ] (Optional) Configure Nginx + SSL
- [ ] Save your `.pem` key file securely

## Useful Commands
```bash
# View live logs
sudo journalctl -u stock-app -f

# Restart app
sudo systemctl restart stock-app

# Update code
cd ~/stock-market && git pull && sudo systemctl restart stock-app

# Check pipeline logs
tail -f ~/stock-market/pipeline.log
```

## Troubleshooting
- **App won't start**: `sudo journalctl -u stock-app -n 50`
- **Out of memory**: Upgrade to t3.small
- **Port blocked**: Check Security Group has port 8000 open
- **Database errors**: `chmod -R 755 ~/stock-market`

---

**🎉 Done!** Your AI stock prediction platform is live on AWS!
