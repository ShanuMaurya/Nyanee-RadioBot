#!/bin/bash

echo "==============================================="
echo "   Rainbow Discord Bot - Oracle VM Setup   "
echo "==============================================="

# 1. Detect OS and install dependencies
if [ -x "$(command -v apt-get)" ]; then
    echo "Detected Ubuntu/Debian based OS."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv ffmpeg git
elif [ -x "$(command -v dnf)" ]; then
    echo "Detected Oracle Linux / RHEL based OS."
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip ffmpeg git
elif [ -x "$(command -v yum)" ]; then
    echo "Detected older Oracle Linux / CentOS based OS."
    sudo yum update -y
    sudo yum install -y python3 python3-pip ffmpeg git
else
    echo "Warning: Could not automatically detect package manager. Please ensure Python3 and FFmpeg are installed."
fi

# 2. Setup Virtual Environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python requirements
echo "Installing Python dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "Error: requirements.txt not found! Make sure you uploaded all bot files."
fi

# 4. Create Systemd Service
echo "Creating Systemd service to run the bot 24/7..."
SERVICE_FILE="/etc/systemd/system/rainbowbot.service"
CURRENT_DIR=$(pwd)
CURRENT_USER=$USER

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Rainbow Discord Radio Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 5. Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable rainbowbot
sudo systemctl start rainbowbot

echo "==============================================="
echo "Setup Complete! The bot is now running in the background."
echo "You can check its status at any time by running:"
echo "sudo systemctl status rainbowbot"
echo "==============================================="
