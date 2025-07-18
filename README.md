# Facial Recognition System

A comprehensive full-stack web application for employee attendance tracking using facial recognition technology.

## Features

- **Real-time Face Recognition**: Advanced facial recognition using InsightFace
- **Role-based Access Control**: Employee, Admin, and Super Admin roles
- **Live Camera Feed**: WebSocket-based real-time video streaming
- **Employee Management**: Complete CRUD operations for employee records
- **Attendance Tracking**: Automated check-in/check-out logging
- **Face Enrollment**: Multi-image face enrollment system
- **Admin Dashboard**: System statistics and monitoring
- **Responsive UI**: Modern, clean interface built with React and Tailwind CSS

## Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance web framework
- **PostgreSQL**: Robust database with SQLAlchemy ORM
- **InsightFace**: State-of-the-art face recognition
- **JWT Authentication**: Secure token-based auth
- **WebSocket Support**: Real-time communication

### Frontend (React/TypeScript)
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Query**: Efficient data fetching
- **React Router**: Client-side routing

### Database Schema
- **employees**: Employee information and metadata
- **face_embeddings**: Facial recognition embeddings
- **attendance_records**: Check-in/check-out logs
- **users**: System user accounts
- **roles**: Role-based permissions
- **system_logs**: Application logging

## Project Structure

```
facial-recognition-system/
├── app/                          # Backend application
│   ├── api/                      # API routes
│   │   ├── routes/              # Route modules
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── employees.py     # Employee management
│   │   │   ├── attendance.py    # Attendance tracking
│   │   │   ├── admin.py         # Admin operations
│   │   │   └── camera.py        # Camera/video streaming
│   │   └── dependencies.py      # Route dependencies
│   ├── core/                    # Core application modules
│   │   ├── config.py           # Configuration settings
│   │   ├── database.py         # Database connection
│   │   └── security.py         # Authentication/security
│   ├── models/                  # Database models
│   │   ├── employee.py         # Employee model
│   │   ├── user.py             # User/role models
│   │   ├── attendance.py       # Attendance models
│   │   └── face_embedding.py   # Face embedding model
│   ├── schemas/                 # Pydantic schemas
│   │   ├── auth.py             # Auth schemas
│   │   ├── employee.py         # Employee schemas
│   │   └── attendance.py       # Attendance schemas
│   ├── services/                # Business logic
│   │   ├── face_recognition_service.py    # Face recognition
│   │   ├── face_enrollment_service.py     # Face enrollment
│   │   └── camera_service.py              # Camera operations
│   └── main.py                  # Application entry point
├── frontend/                    # Frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   ├── contexts/           # React contexts
│   │   ├── hooks/              # Custom hooks
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   └── main.tsx            # Application entry point
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Backend container
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
└── README.md                   # This file
```

## User Roles & Permissions

### Employee
- View own attendance records
- See currently present employees
- Access personal dashboard

### Admin
- All employee permissions
- View all employee attendance
- Enroll new employees
- Manage face embeddings
- Delete employee records
- Access live camera feed
- View system statistics

### Super Admin
- All admin permissions
- Create/delete user accounts
- Manage role assignments
- System administration

## Setup Instructions

### System Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Nginx
- At least 4GB RAM and 20GB disk space

### Production Setup (Recommended)

1. **Prepare the server**
   ```bash
   # Clone the repository to your server
   git clone <your-repository-url>
   cd facial-recognition-system
   ```

2. **Run the setup script**
   ```bash
   # Make setup script executable
   chmod +x setup.sh
   
   # Run setup (will install all dependencies and configure services)
   ./setup.sh
   ```

3. **Access the application**
   ```bash
   # The application will be available at:
   # http://your-server-ip
   
   # Default login credentials:
   # Username: admin
   # Password: admin123
   ```

### Development Setup

1. **Quick development start**
   ```bash
   # Clone repository
   git clone <your-repository-url>
   cd facial-recognition-system
   
   # Copy environment template
   cp .env.example .env
   # Edit .env with your database settings
   
   # Start development servers
   chmod +x start.sh
   ./start.sh
   ```

2. **Manual development setup**
   ```bash
   # Backend setup
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Frontend setup
   cd frontend
   npm install
   cd ..
   
   # Start backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Start frontend (in another terminal)
   cd frontend && npm run dev
   ```

### Database Setup

#### PostgreSQL Installation and Configuration
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE face_tracking;"
sudo -u postgres psql -c "CREATE USER face_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE face_tracking TO face_user;"

# Update .env file with database credentials
```

## Deployment and Management

### Service Management
```bash
# Check service status
sudo systemctl status facial-recognition-backend
sudo systemctl status nginx

# Restart services
sudo systemctl restart facial-recognition-backend
sudo systemctl restart nginx

# View logs
sudo journalctl -u facial-recognition-backend -f
sudo tail -f /var/log/nginx/error.log
```

### Updates and Deployment
```bash
# Deploy updates
chmod +x deploy.sh
./deploy.sh

# Or manually:
cd /opt/facial-recognition
git pull  # if using git
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm run build && cd ..
sudo systemctl restart facial-recognition-backend
```

### File Locations
- **Application**: `/opt/facial-recognition/`
- **Logs**: `/opt/facial-recognition/logs/` and `journalctl -u facial-recognition-backend`
- **Uploads**: `/opt/facial-recognition/uploads/`
- **Nginx Config**: `/etc/nginx/sites-available/facial-recognition`
- **Service Config**: `/etc/systemd/system/facial-recognition-backend.service`

## API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://your-server-ip/api/docs
- ReDoc: http://your-server-ip/api/redoc

### Key Endpoints

#### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/users` - Create user (Super Admin)

#### Employees
- `GET /api/employees` - List employees
- `POST /api/employees` - Create employee
- `POST /api/employees/{id}/enroll` - Enroll face images
- `DELETE /api/employees/{id}` - Delete employee

#### Attendance
- `GET /api/attendance` - Get attendance records
- `GET /api/attendance/present` - Get present employees
- `GET /api/attendance/employee/{id}` - Get employee attendance

#### Camera
- `GET /api/camera/status` - Get camera status
- `POST /api/camera/start` - Start camera processing
- `WebSocket /api/camera/feed` - Live video feed

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_NAME` | Database name | face_tracking |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | password |
| `SECRET_KEY` | JWT secret key | (required) |
| `DEBUG` | Debug mode | True |
| `FACE_DETECTION_THRESHOLD` | Face detection threshold | 0.6 |
| `FACE_RECOGNITION_THRESHOLD` | Face recognition threshold | 0.4 |

### Camera Configuration
- Camera ID (default: 0 for default camera)
- Resolution (default: 640x480)
- FPS target (default: 30)
- Detection/recognition thresholds

## Deployment

### Production Configuration

1. **Security Configuration**
   ```bash
   # Edit /opt/facial-recognition/.env
   DEBUG=False
   SECRET_KEY=your-secure-secret-key
   DB_PASSWORD=secure-database-password
   ```

2. **SSL/HTTPS Setup** (Recommended)
   ```bash
   # Install Certbot for Let's Encrypt
   sudo apt install certbot python3-certbot-nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d your-domain.com
   ```

3. **Firewall Configuration**
   ```bash
   # Configure UFW firewall
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

### Security Considerations

- Change default passwords
- Use strong JWT secret keys
- Enable HTTPS with SSL certificates
- Configure firewall rules
- Regular security updates
- Database access restrictions
- Limit file upload sizes
- Regular backup procedures

## Troubleshooting

### Common Issues

1. **Camera not detected**
   - Check camera permissions
   - Verify camera ID in configuration
   - Ensure no other applications are using the camera

2. **Face recognition not working**
   - Verify InsightFace installation
   - Check CUDA availability for GPU acceleration
   - Ensure sufficient lighting for face detection

3. **Database connection errors**
   - Verify PostgreSQL is running
   - Check connection parameters
   - Ensure database exists

4. **WebSocket connection issues**
   - Check firewall settings
   - Verify proxy configuration
   - Ensure WebSocket support in browser

### Logs and Monitoring

- **Application logs**: 
  ```bash
  sudo journalctl -u facial-recognition-backend -f
  tail -f /opt/facial-recognition/logs/app.log
  ```
- **Nginx logs**: 
  ```bash
  sudo tail -f /var/log/nginx/access.log
  sudo tail -f /var/log/nginx/error.log
  ```
- **Database logs**: 
  ```bash
  sudo tail -f /var/log/postgresql/postgresql-*.log
  ```
- **System monitoring**: Available through admin interface

### Performance Optimization

- **Database**: Regular VACUUM and ANALYZE operations
- **File Storage**: Regular cleanup of old uploaded files
- **Memory**: Monitor memory usage, especially for face recognition operations
- **CPU**: Consider GPU acceleration for face recognition if available

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the documentation
- Review existing issues
- Create a new issue with detailed information
- Include logs and system information

## Acknowledgments

- InsightFace for face recognition technology
- FastAPI for the excellent web framework
- React and Tailwind CSS for the frontend
- PostgreSQL for reliable data storage