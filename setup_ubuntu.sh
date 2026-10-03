#!/bin/bash

# Exit script if any command fails
set -e

echo "🚀 Starting deployment setup for Satilite Engine..."

# Update packages and ensure essential tools are installed
echo "📦 Installing required system packages (Python, Node, npm)..."
sudo apt update
sudo apt install -y python3-venv python3-pip npm

# Ensure pm2 is installed globally
if ! command -v pm2 &> /dev/null
then
    echo "📦 Installing pm2 globally..."
    sudo npm install -g pm2
fi

# ==========================================
# 1. SET UP BACKEND
# ==========================================
echo "🐍 Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt
deactivate

# Start backend using pm2 on port 8899
echo "🚀 Starting backend on port 8899 with PM2..."
# Stop it if it's already running to restart fresh
pm2 delete satilites-backend 2>/dev/null || true
pm2 start "./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8899" --name "satilites-backend"

# Go back to root directory
cd ..


# ==========================================
# 2. SET UP FRONTEND
# ==========================================
echo "⚛️ Setting up Frontend..."
cd frontend

# Install dependencies and build for production
npm install
npm run build

# Start frontend using pm2 to serve the static build on port 9898
echo "🚀 Starting frontend on port 9898 with PM2..."
# Stop it if it's already running to restart fresh
pm2 delete satilites-frontend 2>/dev/null || true
pm2 serve dist 9898 --name "satilites-frontend" --spa

# Go back to root directory
cd ..


# ==========================================
# 3. FINALIZE
# ==========================================
# Save PM2 state so it restarts automatically if the server reboots
pm2 save

# Setup PM2 startup script if not already done (Optional but recommended)
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp $HOME || true

echo ""
echo "✅ Setup complete! PM2 is now managing your apps."
echo "=================================================="
echo "🔹 Backend API is running on : http://<your-server-ip>:8899"
echo "🔹 Frontend App is running on: http://<your-server-ip>:9898"
echo "=================================================="
echo ""
echo "Helpful PM2 commands:"
echo "- 'pm2 status' : View all running apps"
echo "- 'pm2 logs'   : View live logs for both apps"
echo "- 'pm2 restart satilites-frontend' : Restart the frontend"
