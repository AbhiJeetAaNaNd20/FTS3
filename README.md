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

### Prerequisites
- Docker and Docker Compose
- Python 3.10+ (for local development)
- Node.js 18+ (for frontend development)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd facial-recognition-system
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the application**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

5. **Default login credentials**
   - Username: `admin`
   - Password: `admin123`

### Local Development Setup

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=face_tracking
export DB_USER=postgres
export DB_PASSWORD=password
export SECRET_KEY=your-secret-key

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

#### Database Setup
```bash
# Start PostgreSQL (using Docker)
docker run -d \
  --name postgres-face-recognition \
  -e POSTGRES_DB=face_tracking \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# Database tables will be created automatically on first run
```

## API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

### Production Deployment

1. **Update environment variables**
   ```bash
   # Set production values
   export DEBUG=False
   export SECRET_KEY=your-production-secret-key
   export DB_PASSWORD=secure-production-password
   ```

2. **Build and deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up reverse proxy** (nginx example)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
       
       location /api/camera/feed {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

### Security Considerations

- Change default passwords
- Use strong JWT secret keys
- Enable HTTPS in production
- Configure firewall rules
- Regular security updates
- Database access restrictions

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

- Application logs: `logs/app.log`
- Database logs: Check PostgreSQL logs
- System logs: Available through admin interface
- Performance monitoring: Built-in metrics in admin dashboard

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