#!/bin/bash

# Deployment script for updates
# Run this after making changes to the application

set -e

APP_DIR="/opt/facial-recognition"

echo "🔄 Deploying updates to Facial Recognition System..."

# Navigate to app directory
cd $APP_DIR

# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using git)
if [ -d ".git" ]; then
    echo "📥 Pulling latest changes..."
    git pull
fi

# Update Python dependencies
echo "📦 Updating Python dependencies..."
pip install -r requirements.txt

# Update frontend
echo "🎨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Run database migrations if needed
echo "🗄️ Running database migrations..."
python -c "
from app.core.database import create_tables
try:
    create_tables()
    print('✅ Database schema updated')
except Exception as e:
    print(f'⚠️ Database migration warning: {e}')
"

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart facial-recognition-backend
sudo systemctl reload nginx

# Check status
echo "✅ Checking service status..."
sudo systemctl status facial-recognition-backend --no-pager -l

echo ""
echo "🎉 Deployment completed successfully!"
echo "📊 Check logs: sudo journalctl -u facial-recognition-backend -f"