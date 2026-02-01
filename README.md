# FinSight AI - Backend API

> Intelligent expense tracking API with AI-powered categorization, real-time insights, and budget management

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Latest-success.svg)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![API Docs](https://img.shields.io/badge/API-Swagger-orange.svg)](https://api.finsightfinance.me/api/docs)

**Live API:** [https://api.finsightfinance.me](https://api.finsightfinance.me)  
**API Documentation:** [https://api.finsightfinance.me/api/docs](https://api.finsightfinance.me/api/docs)  
**Frontend Repository:** [finsight_ai_frontend](https://github.com/Pranavchikte/finsight_ai_frontend)

---

## Overview

FinSight AI Backend is a production-ready RESTful API built with Flask that powers an intelligent expense tracking platform. It leverages Google's Gemini AI for natural language expense categorization, implements asynchronous task processing with Celery, and provides real-time financial insights.

### Key Features

- **AI-Powered Expense Processing** - Natural language to structured expense data using Gemini AI
- **Asynchronous Task Queue** - Non-blocking AI processing with Celery and Redis
- **Secure Authentication** - JWT-based auth with token refresh and blacklisting
- **Real-time Analytics** - Spending summaries, budget tracking, and trend analysis
- **Timezone-Aware** - Accurate date handling across timezones (UTC storage, IST display)
- **Interactive API Docs** - Auto-generated Swagger/OpenAPI documentation
- **Docker Ready** - Containerized deployment with Docker Compose
- **Production Security** - MongoDB authentication, Redis isolation, password hashing

---

## Screenshots

### API Documentation (Swagger UI)
![API Documentation](./screenshots/api_doc.jpg)

### Dashboard with AI Processing
![Dashboard](./screenshots/dashboard-ai.jpg)

### Transaction History
![Transaction History](./screenshots/transaction-history.jpg)

---

## Performance Metrics

Measured from Digital Ocean production environment:

| Endpoint | Response Time | Notes |
|----------|--------------|-------|
| `GET /api/transactions/categories` | **124ms** | Predefined category list |
| `POST /api/auth/login` | **85ms** | JWT token generation |
| `GET /api/transactions/` | **195-417ms** | Paginated transaction list |
| `GET /api/transactions/summary` | **213ms** | Monthly spending aggregate |
| `POST /api/transactions/` (AI) | **202 (Async)** | Background processing via Celery |

**Infrastructure:**
- **Hosting:** Digital Ocean Droplet (Docker containers)
- **Database:** MongoDB 7.0 with indexed queries
- **Cache/Queue:** Redis 7.0
- **Task Processing:** Celery with solo pool

---

## Architecture
```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  Flask API   │─────▶│   MongoDB   │
│ (Frontend)  │      │  (Gunicorn)  │      │  (Storage)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐      ┌─────────────┐
                     │    Redis     │─────▶│   Celery    │
                     │ (Broker/Cache│      │  (Workers)  │
                     └──────────────┘      └─────────────┘
                                                  │
                                                  ▼
                                           ┌─────────────┐
                                           │  Gemini AI  │
                                           │   (Google)  │
                                           └─────────────┘
```

**Request Flow:**
1. Client sends authenticated request to Flask API
2. API validates JWT token (checks Redis blocklist)
3. For AI expenses: Task queued to Celery, immediate 202 response
4. Celery worker processes task with Gemini AI
5. Result stored in MongoDB, frontend polls for status
6. Regular endpoints return data from MongoDB with proper timezone conversion

---

## 🛠️ Tech Stack

### Core Framework
- **Flask 3.1** - Lightweight WSGI web application framework
- **Gunicorn 23.0** - Production WSGI server with worker management
- **Flask-PyMongo 2.3** - MongoDB integration for Flask
- **Flask-JWT-Extended 4.7** - JWT authentication with refresh tokens

### AI & Task Processing
- **Google Generative AI (Gemini)** - Natural language expense categorization
- **Celery 5.4** - Distributed task queue for async AI processing
- **Redis 5.2** - Message broker and token blacklist storage

### Security & Validation
- **Flask-Bcrypt 1.0** - Password hashing (bcrypt algorithm)
- **Pydantic 2.10** - Request/response validation with type safety
- **Flask-CORS 5.0** - Cross-origin resource sharing

### Documentation & Utilities
- **Flasgger 0.9.7** - Swagger/OpenAPI interactive documentation
- **Flask-Mail 0.10** - Email notifications (password reset)
- **Python-dotenv 1.0** - Environment variable management

---

## Project Structure
```
finsight_ai_backend/
├── app/
│   ├── __init__.py              # Flask app factory, extensions init
│   ├── celery_utils.py          # Celery configuration
│   ├── utils.py                 # Helper functions (response formatting, tokens)
│   ├── auth/
│   │   ├── routes.py            # Authentication endpoints
│   │   └── schemas.py           # Pydantic validation schemas
│   ├── transactions/
│   │   ├── routes.py            # Transaction CRUD endpoints
│   │   ├── schemas.py           # Transaction validation
│   │   └── tasks.py             # Celery tasks for AI processing
│   ├── budgets/
│   │   ├── routes.py            # Budget management endpoints
│   │   └── schemas.py           # Budget validation
│   ├── ai/
│   │   └── routes.py            # AI summary generation
│   ├── models/
│   │   ├── user.py              # User data model
│   │   └── transaction.py       # Transaction data model
│   └── services/
│       └── gemini_service.py    # Gemini AI integration
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── test_auth.py             # Authentication tests
│   └── test_transactions.py     # Transaction endpoint tests
├── logs/                        # Application logs (rotating)
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Container image definition
├── celery_worker.py             # Celery worker entry point
├── config.py                    # Application configuration
├── run.py                       # Development server entry
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## Getting Started

### Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **MongoDB 7.0+** ([Installation Guide](https://www.mongodb.com/docs/manual/installation/))
- **Redis 7.0+** ([Installation Guide](https://redis.io/docs/install/install-redis/))
- **Docker & Docker Compose** (Optional, for containerized deployment)

### Environment Variables

Create a `.env.local` file in the project root:
```bash
# Database
MONGO_URI=mongodb://admin:password@localhost:27017/finsight_db?authSource=admin

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this

# AI Service
GEMINI_API_KEY=your-google-gemini-api-key

# Task Queue
BROKER_URL=redis://localhost:6379/0
RESULT_BACKEND=redis://localhost:6379/0

# Email (Optional - for password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Local Development Setup
```bash
# 1. Clone the repository
git clone https://github.com/Pranavchikte/finsight_ai_backend.git
cd finsight_ai_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start MongoDB and Redis (if not running)
# macOS with Homebrew:
brew services start mongodb-community
brew services start redis

# Linux:
sudo systemctl start mongod
sudo systemctl start redis

# 5. Run Flask development server
python run.py

# 6. In a new terminal, start Celery worker
celery -A celery_worker.celery worker --loglevel=info
```

The API will be available at `http://localhost:5000`  
API Documentation: `http://localhost:5000/api/docs`

---

## Docker Deployment

### Quick Start with Docker Compose
```bash
# 1. Clone and navigate to project
git clone https://github.com/Pranavchikte/finsight_ai_backend.git
cd finsight_ai_backend

# 2. Create .env file with production settings
cp .env.example .env
# Edit .env with your production credentials

# 3. Build and start all services
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

**Services Started:**
- `finsight-backend` - Flask API on port 5000
- `finsight-celery-worker` - Background task processor
- `finsight-mongo` - MongoDB database (internal only)
- `finsight-redis` - Redis cache/broker (internal only)

### Production Deployment Checklist

- [ ] Set strong `JWT_SECRET_KEY` (32+ random characters)
- [ ] Configure MongoDB authentication
- [ ] Use environment-specific `.env` file
- [ ] Enable HTTPS with reverse proxy (Nginx/Caddy)
- [ ] Set up firewall rules (expose only port 5000)
- [ ] Configure log rotation and monitoring
- [ ] Set up automated backups for MongoDB
- [ ] Use Docker secrets for sensitive data

---

## API Documentation

### Interactive Documentation

Visit [https://api.finsightfinance.me/api/docs](https://api.finsightfinance.me/api/docs) for:
- ✅ Interactive endpoint testing
- ✅ Request/response schemas
- ✅ JWT authentication testing
- ✅ Example requests with curl/Python

### Core Endpoints

#### Authentication
```http
POST /api/auth/register        # Create new user account
POST /api/auth/login           # Login and get JWT tokens
POST /api/auth/refresh         # Refresh access token
DELETE /api/auth/logout        # Revoke token (add to blocklist)
POST /api/auth/forgot-password # Request password reset email
POST /api/auth/reset-password  # Reset password with token
GET  /api/auth/profile         # Get/update user profile
```

#### Transactions
```http
GET    /api/transactions/              # List transactions (paginated, filterable)
POST   /api/transactions/              # Add expense (manual or AI mode)
GET    /api/transactions/:id           # Get single transaction
DELETE /api/transactions/:id           # Delete transaction
GET    /api/transactions/summary       # Monthly spending summary
GET    /api/transactions/history       # Transactions grouped by day
GET    /api/transactions/:id/status    # Check AI processing status
GET    /api/transactions/categories    # List predefined categories
```

#### Budgets
```http
GET    /api/budgets/           # List user's budgets
POST   /api/budgets/           # Create new budget
GET    /api/budgets/:id        # Get budget details
PUT    /api/budgets/:id        # Update budget
DELETE /api/budgets/:id        # Delete budget
```

#### AI Insights
```http
POST /api/ai/summary           # Generate AI spending insights (async)
GET  /api/ai/summary/result/:task_id  # Poll for summary result
```

### Example: AI Expense Processing
```bash
# 1. Add expense with natural language
curl -X POST https://api.finsightfinance.me/api/transactions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "ai",
    "text": "Bought groceries from Walmart for $45.50"
  }'

# Response (202 Accepted - Processing)
{
  "status": "success",
  "data": {
    "_id": "507f1f77bcf86cd799439011",
    "status": "processing",
    "date": "2026-02-01T06:30:00+00:00"
  }
}

# 2. Poll for status
curl https://api.finsightfinance.me/api/transactions/507f1f77bcf86cd799439011/status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response (after processing)
{
  "status": "success",
  "data": {
    "_id": "507f1f77bcf86cd799439011",
    "amount": 45.50,
    "category": "Groceries",
    "description": "Groceries from Walmart",
    "status": "completed",
    "date": "2026-02-01T06:30:00+00:00"
  }
}
```

---

## Testing
```bash
# Run all tests with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v

# Run with detailed output
pytest -vv
```

**Test Coverage:**
- ✅ Authentication flow (register, login, refresh, logout)
- ✅ Transaction CRUD operations
- ✅ AI expense processing (mocked Gemini responses)
- ✅ Budget management
- ✅ Input validation and error handling
- ✅ JWT token expiration and blacklisting

---

## Security Features

### Implemented Security Measures

1. **Password Security**
   - Bcrypt hashing with salt (cost factor 12)
   - Minimum 8 characters with complexity requirements
   - Secure password reset via email tokens (1-hour expiry)

2. **Authentication & Authorization**
   - JWT tokens with 15-min access / 7-day refresh expiry
   - Token blacklisting on logout (Redis-based)
   - Refresh token rotation
   - Protected routes with `@jwt_required()` decorator

3. **Database Security**
   - MongoDB authentication with role-based access
   - Parameterized queries (no SQL injection risk)
   - Connection encryption (TLS/SSL in production)

4. **Network Security**
   - CORS configured for specific frontend origins
   - MongoDB/Redis ports not exposed (Docker internal network)
   - Rate limiting on sensitive endpoints (login, register)

5. **Input Validation**
   - Pydantic schemas for all request bodies
   - Type checking and data sanitization
   - Email validation with regex patterns

---

## Environment Configuration

The app supports environment-specific configurations:
```python
# Development (default)
FLASK_ENV=development
python run.py

# Production
FLASK_ENV=production
gunicorn run:app --bind 0.0.0.0:5000
```

**Configuration Hierarchy:**
1. Environment variables (highest priority)
2. `.env.production` (if `FLASK_ENV=production`)
3. `.env.local` (development default)
4. `config.py` fallback values

---

## 📈 Monitoring & Logging

### Application Logs
```bash
# Logs stored in logs/app.log with rotation
tail -f logs/app.log

# Docker logs
docker logs finsight-backend -f --tail 100
```

### Health Check
```bash
curl https://api.finsightfinance.me/health

# Response
{
  "status": "healthy"
}
```

Checks:
- ✅ MongoDB connection
- ✅ Redis connection
- ✅ API responsiveness

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Code Standards:**
- Follow PEP 8 style guide
- Add docstrings to all functions
- Write tests for new features
- Update API documentation (Swagger docstrings)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Pranav Chikte**  
- GitHub: [@Pranavchikte](https://github.com/Pranavchikte)
- LinkedIn: [Pranav Chikte](https://www.linkedin.com/in/pranav-chikte)
- Email: chiktepranav1378@gmail.com

---

## Acknowledgments

- **Google Gemini AI** for natural language processing
- **Flask** community for excellent documentation
- **MongoDB** for flexible document storage
- **Celery** for reliable task queue implementation
- **Digital Ocean** for hosting infrastructure

---

## Related Links

- **Frontend Repository:** [finsight_ai_frontend](https://github.com/Pranavchikte/finsight_ai_frontend)
- **Live Application:** [https://www.finsightfinance.me](https://www.finsightfinance.me)
- **API Documentation:** [https://api.finsightfinance.me/api/docs](https://api.finsightfinance.me/api/docs)

---

<p align="center">Made with ❤️ by Pranav Chikte</p>
