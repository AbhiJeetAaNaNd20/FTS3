#!/bin/bash

# Facial Recognition System Setup Script
# Run this script on your Linux server to set up the application

set -e

echo "🚀 Setting up Facial Recognition System..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons"
   echo "Please run as a regular user with sudo privileges"
   exit 1
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    nodejs \
    npm \
    git \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1

# Install Node.js 18+ if needed
echo "📦 Installing Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Create application directory
APP_DIR="/opt/facial-recognition"
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files (assuming they're in current directory)
echo "📋 Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
python3.10 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Setup PostgreSQL database
echo "🗄️ Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE face_tracking;" || echo "Database might already exist"
sudo -u postgres psql -c "CREATE USER face_user WITH PASSWORD 'secure_password_123';" || echo "User might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE face_tracking TO face_user;"
sudo -u postgres psql -c "ALTER USER face_user CREATEDB;"

# Create database tables and initial data
echo "🏗️ Creating database schema..."
python -c "
from app.core.database import create_tables
from app.core.security import get_password_hash
from app.core.database import SessionLocal
from app.models.user import User, Role

# Create tables
create_tables()

# Create initial roles and admin user
db = SessionLocal()
try:
    # Create roles
    roles_data = [
        ('employee', '{\"view_own_attendance\": true, \"view_present_employees\": true}'),
        ('admin', '{\"view_all_attendance\": true, \"enroll_employees\": true, \"manage_embeddings\": true, \"delete_employees\": true, \"view_camera_feed\": true}'),
        ('super_admin', '{\"view_all_attendance\": true, \"enroll_employees\": true, \"manage_embeddings\": true, \"delete_employees\": true, \"view_camera_feed\": true, \"manage_users\": true, \"manage_roles\": true}')
    ]
    
    for role_name, permissions in roles_data:
        existing_role = db.query(Role).filter(Role.role_name == role_name).first()
        if not existing_role:
            role = Role(role_name=role_name, permissions=permissions)
            db.add(role)
    
    db.commit()
    
    # Create admin user
    admin_role = db.query(Role).filter(Role.role_name == 'super_admin').first()
    existing_admin = db.query(User).filter(User.username == 'admin').first()
    
    if not existing_admin and admin_role:
        admin_user = User(
            username='admin',
            password_hash=get_password_hash('admin123'),
            role_id=admin_role.id
        )
        db.add(admin_user)
        db.commit()
        print('✅ Created admin user: admin/admin123')
    else:
        print('ℹ️ Admin user already exists')
        
except Exception as e:
    print(f'❌ Error setting up database: {e}')
    db.rollback()
finally:
    db.close()
"

# Create directories
echo "📁 Creating required directories..."
mkdir -p uploads logs

# Set up frontend
echo "🎨 Setting up frontend..."
cd frontend
npm install
npm run build
cd ..

# Create systemd service for backend
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/facial-recognition-backend.service > /dev/null <<EOF
[Unit]
Description=Facial Recognition Backend
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/facial-recognition > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;
    
    # Frontend
    location / {
        root $APP_DIR/frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket for camera feed
    location /api/camera/feed {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/facial-recognition /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Create environment file
echo "🔧 Creating environment configuration..."
cat > .env <<EOF
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=face_tracking
DB_USER=face_user
DB_PASSWORD=secure_password_123

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=False
CORS_ORIGINS=http://localhost

# Face Recognition
FACE_DETECTION_THRESHOLD=0.6
FACE_RECOGNITION_THRESHOLD=0.4

# File Storage
UPLOAD_DIR=$APP_DIR/uploads
MAX_FILE_SIZE=10485760
EOF

# Set proper permissions
echo "🔒 Setting permissions..."
sudo chown -R $USER:$USER $APP_DIR
chmod +x $APP_DIR/venv/bin/*
chmod 755 $APP_DIR/uploads
chmod 755 $APP_DIR/logs

# Start and enable services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable facial-recognition-backend
sudo systemctl start facial-recognition-backend
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Check service status
echo "✅ Checking service status..."
sudo systemctl status facial-recognition-backend --no-pager -l
sudo systemctl status nginx --no-pager -l

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Access the application at: http://your-server-ip"
echo "2. Login with: admin / admin123"
echo "3. Change the default password immediately"
echo ""
echo "🔧 Useful Commands:"
echo "- Check backend logs: sudo journalctl -u facial-recognition-backend -f"
echo "- Check nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "- Restart backend: sudo systemctl restart facial-recognition-backend"
echo "- Restart nginx: sudo systemctl restart nginx"
echo ""
echo "📁 Application directory: $APP_DIR"
echo "🗄️ Database: PostgreSQL (face_tracking)"
echo "🌐 Web server: Nginx on port 80"
echo "🔌 Backend API: Port 8000"