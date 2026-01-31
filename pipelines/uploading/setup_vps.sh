#!/bin/bash

# Deka Scraper VPS Setup Script (Ubuntu 20.04/22.04)

echo "🚀 Starting VPS Setup for Deka Scraper..."

# 1. Update Packages
echo "📦 Updating Package Lists..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Node.js (Version 18.x recommended)
echo "🟢 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v
npm -v

# 3. Install Puppeteer System Dependencies
# These are required to run Headless Chrome on a server without a GUI
echo "🔧 Installing Chrome Dependencies..."
sudo apt-get install -y ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils

# 4. Install Project Dependencies
echo "📚 Installing Project Modules..."
npm install puppeteer

# 5. Setup Screen (for background running)
sudo apt-get install -y screen

echo "✅ Setup Complete!"
echo "To run the scraper: node launcher_vps.js"
echo "Or run in background: screen -S deka node launcher_vps.js"
