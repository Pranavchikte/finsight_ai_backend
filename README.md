# FinSight AI Backend

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1.2-000000?style=flat&logo=flask&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL-47A248?style=flat&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=flat&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-Task%20Queue-B49C5C?style=flat&logo=celery&logoColor=white)
![Gemini AI](https://img.shields.io/badge/Google-Gemini%20AI-4285F4?style=flat&logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

> Production-ready Flask REST API powering intelligent expense tracking with AI-powered categorization, budget management, and real-time insights.

## Live Demo

**Frontend Application:** [https://www.finsightfinance.me](https://www.finsightfinance.me)

**API Documentation:** [https://api.finsightfinance.me/api/docs](https://api.finsightfinance.me/api/docs)

**Backend API:** [https://api.finsightfinance.me](https://api.finsightfinance.me)

---

## Table of Contents

- [About](#about)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [Testing](#testing)
- [Security Features](#security-features)
- [System Design](#system-design)
- [Future Enhancements](#future-enhancements)

---

## About

FinSight AI is an intelligent expense tracking platform that automates transaction logging using GenAI. It transforms how users manage their finances by:

- Converting natural language inputs into structured transactions
- Providing AI-powered spending insights and recommendations
- Enabling smart budget management with real-time tracking
- Delivering personalized financial advice based on spending patterns

This backend powers the production application serving real users with features designed for scale, security, and performance.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FinSight AI Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│   │   Frontend   │────▶│   Flask API   │────▶│   MongoDB     │             │
│   │  (Next.js)   │     │  (Gunicorn)   │     │  (Database)   │             │
│   │              │     │              │     │               │             │
│   │ https://     │     │ https://     │     │               │             │
│   │ finsight     │     │ api.finsight │     │               │             │
│   │ finance.me   │     │ finance.me   │     │               │             │
│   └──────────────┘     └──────┬───────┘     └──────────────┘             │
│                               │                                              │
│                               ▼                                              │
│                        ┌──────────────┐                                    │
│                        │    Redis     │                                    │
│                        │  (Celery +   │                                    │
│                        │   Cache)     │                                    │
│                        └──────┬───────┘                                    │
│                               │                                              │
│                               ▼                                              │
│                        ┌──────────────┐       ┌──────────────┐           │
│                        │  Celery       │────▶  │  Gemini AI   │           │
│                        │  Workers      │       │  (LLM)       │           │
│                        │  (Async)      │       │              │           │
│                        └──────────────┘       └──────────────┘           │
│                                                                             │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │                        SendGrid Email Service                       │   │
│   └────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Request Flow

1. User interacts with Next.js frontend
2. Frontend sends authenticated requests to Flask API
3. API validates JWT tokens and processes requests
4. For AI tasks: request is queued to Celery via Redis
5. Celery workers process AI tasks asynchronously
6. Gemini AI processes natural language or generates insights
7. Results are stored in MongoDB
8. Frontend polls for results or receives real-time updates

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Runtime** | Python | 3.11+ | Backend runtime environment |
| **Framework** | Flask | 3.1.2 | REST API framework |
| **Database** | MongoDB | Latest | NoSQL document database |
| **Cache/Message Broker** | Redis | Latest | Celery broker & token blacklist |
| **Task Queue** | Celery | 5.5.3 | Async AI processing |
| **AI/ML** | Google Gemini | 2.5-flash | Expense parsing & insights |
| **Authentication** | JWT | PyJWT 2.10.1 | Secure token-based auth |
| **Email** | SendGrid | 6.12.5 | Transactional emails |
| **API Docs** | Flasgger | 0.9.7.1 | Swagger documentation |
| **Deployment** | Docker | Latest | Containerization |
| **Process Manager** | Gunicorn | 23.0.0 | WSGI application server |
| **Testing** | Pytest | 8.4.2 | Unit & integration tests |

---

## Project Structure

```
finsight_ai_backend/
├── app/
│   ├── __init__.py              # Flask app factory, extensions, blueprints
│   ├── celery_utils.py          # Celery configuration
│   ├── config.py                # Environment-based configuration
│   ├── email_sendgrid.py       # SendGrid email service wrapper
│   ├── utils.py                # Shared utilities & helpers
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py           # Auth endpoints (register, login, logout, refresh)
│   │   └── schemas.py          # Pydantic validation schemas
│   │
│   ├── transactions/
│   │   ├── __init__.py
│   │   ├── routes.py           # CRUD operations, filtering, pagination
│   │   ├── schemas.py          # Transaction validation schemas
│   │   └── tasks.py            # Celery tasks for AI processing
│   │
│   ├── budgets/
│   │   ├── __init__.py
│   │   ├── routes.py           # Budget management endpoints
│   │   └── schemas.py          # Budget validation schemas
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   └── routes.py           # AI summary endpoints
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model & password hashing
│   │   └── transaction.py     # Transaction model
│   │
│   ├── services/
│   │   └── gemini_service.py   # Gemini AI integration
│   │
│   └── tasks/
│       └── email_tasks.py      # Async email tasks
│
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_auth.py            # Authentication tests
│   └── test_transactions.py    # Transaction tests
│
├── logs/                       # Application logs
├── celery_worker.py            # Celery worker entry point
├── config.py                   # Configuration file
├── docker-compose.yml          # Multi-container orchestration
├── Dockerfile                  # Backend container image
├── pytest.ini                  # Pytest configuration
├── requirements.txt            # Python dependencies
└── run.py                     # Application entry point
```

---

## Features

### Authentication & Security
- JWT-based authentication with access & refresh tokens
- Token blacklisting for secure logout
- Password strength validation (8+ chars, uppercase, number, special char)
- Email normalization to prevent duplicates
- Rate limiting on login endpoints
- Generic error messages to prevent enumeration attacks

### Transaction Management
- Manual transaction entry with 12 predefined categories
- AI-powered natural language expense parsing
- Advanced filtering (category, amount range, date range)
- Search by description
- Pagination with configurable limits (max 100)
- Transaction status tracking (processing/completed/failed)

### AI-Powered Features

#### Smart Expense Parsing
Converts natural language to structured transactions:

```
Input:  "lunch with the team yesterday for 1500.50 rupees at the cafe"
Output: {"amount": 1500.50, "category": "Food & Dining", "description": "Lunch with team at the cafe"}

Input:  "uber ride to the airport for 750rs"
Output: {"amount": 750.00, "category": "Transportation", "description": "Uber ride to the airport"}
```

#### Spending Insights
AI-generated monthly summaries with actionable tips:
- Identifies top spending categories
- Provides personalized saving recommendations
- Encouraging, non-judgmental tone

#### Spam Prevention
- Active task tracking per user
- Prevents duplicate AI processing requests

### Budget Management
- Create monthly budgets by category
- Real-time spending vs. budget tracking
- Automatic aggregation of category spending
- Visual progress indicators
- Future budget validation (current + next month only)

### Email Notifications
- Password reset via SendGrid
- Async email delivery with Celery
- Branded HTML email templates

### Health Monitoring
- `/health` endpoint for container orchestration
- Database and Redis connectivity checks

---

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Create new account | No |
| POST | `/login` | Authenticate user | No |
| POST | `/logout` | Revoke tokens | Yes |
| POST | `/refresh` | Get new access token | Yes (refresh) |
| POST | `/forgot-password` | Request password reset | No |
| POST | `/reset-password` | Reset password with token | No |
| GET | `/profile` | Get user profile | Yes |
| POST | `/profile` | Update income | Yes |

### Transactions (`/api/transactions`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Add transaction (manual/AI) | Yes |
| GET | `/` | List transactions (paginated, filtered) | Yes |
| GET | `/summary` | Current month spending | Yes |
| GET | `/history` | Daily spending history | Yes |
| GET | `/categories` | List predefined categories | No |
| GET | `/<id>` | Get single transaction | Yes |
| DELETE | `/<id>` | Delete transaction | Yes |
| GET | `/<id>/status` | Check AI processing status | Yes |

### Budgets (`/api/budgets`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/` | Create budget | Yes |
| GET | `/` | Get current month budgets with spending | Yes |

### AI (`/api/ai`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/summary` | Trigger AI spending summary | Yes |
| GET | `/summary/result/<task_id>` | Get summary result | Yes |

---

## Getting Started

### Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- Redis
- Google Gemini API key

### Local Development Setup

1. **Clone the repository**
   ```bash
   cd finsight_ai_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment variables**
   Create a `.env` file:
   ```env
   MONGO_URI=mongodb://localhost:27017/finsight_db
   JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters
   GEMINI_API_KEY=your-gemini-api-key
   FRONTEND_URL=http://localhost:3000
   BROKER_URL=redis://localhost:6379/0
   RESULT_BACKEND=redis://localhost:6379/0
   SENDGRID_API_KEY=your-sendgrid-api-key
   FROM_EMAIL=noreply@yourdomain.com
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Run Celery worker (separate terminal)**
   ```bash
   celery -A celery_worker.celery worker --loglevel=info -P solo
   ```

7. **Access API**
   - API: http://localhost:5000
   - Swagger Docs: http://localhost:5000/api/docs
   - Health Check: http://localhost:5000/health

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGO_URI` | Yes | MongoDB connection string |
| `JWT_SECRET_KEY` | Yes | Secret key for JWT signing (min 32 chars) |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `FRONTEND_URL` | Yes | Frontend URL for CORS |
| `BROKER_URL` | Yes | Redis connection for Celery |
| `RESULT_BACKEND` | Yes | Redis connection for task results |
| `SENDGRID_API_KEY` | No | SendGrid API key for emails |
| `FROM_EMAIL` | No | Sender email address |

---

## Docker Deployment

### Quick Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services Created

| Service | Port | Description |
|---------|------|-------------|
| mongo | 27017 | MongoDB database |
| redis | 6379 | Redis cache & message broker |
| backend | 5000 | Flask API server |
| celery-worker | - | Async task processor |

### Production Deployment

```bash
# Build production image
docker build -t finsight-backend:latest .

# Run with environment variables
docker run -d \
  --name finsight-backend \
  -p 5000:5000 \
  -e MONGO_URI=mongodb://mongo:27017/finsight_db \
  -e BROKER_URL=redis://redis:6379/0 \
  -e JWT_SECRET_KEY=your-secret \
  -e GEMINI_API_KEY=your-key \
  finsight-backend:latest
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run tests in watch mode
pytest -w
```

### Test Coverage

- Authentication (register, login, logout, refresh)
- Transaction CRUD operations
- Input validation
- Error handling

---

## Security Features

### Implemented Security Measures

1. **Password Security**
   - Bcrypt hashing with salt
   - Strength validation (8+ chars, uppercase, number, special)
   - Generic error messages

2. **Token Management**
   - Short-lived access tokens (15 min)
   - Long-lived refresh tokens (7 days)
   - Token blacklisting for logout
   - JTI (JWT ID) for tracking

3. **API Security**
   - CORS whitelisting (production domains)
   - Input validation with Pydantic
   - Rate limiting on auth endpoints
   - SQL injection prevention (MongoDB queries)

4. **Data Protection**
   - Email enumeration prevention
   - IDOR protection (ownership checks)
   - Request timeout limits (30s)

---

## System Design

### Database Schema

#### Users Collection
```json
{
  "_id": "ObjectId",
  "email": "string (unique, lowercase)",
  "password": "string (bcrypt hash)",
  "income": "number",
  "created_at": "datetime"
}
```

#### Transactions Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "amount": "number",
  "category": "string",
  "description": "string",
  "date": "datetime",
  "status": "string (processing/completed/failed)",
  "raw_text": "string (AI mode input)",
  "failure_reason": "string (on failure)"
}
```

#### Budgets Collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "category": "string",
  "limit": "number",
  "month": "number",
  "year": "number",
  "created_at": "datetime"
}
```

### Indexes

```javascript
db.users.createIndex("email", { unique: true })
db.transactions.createIndex("user_id")
db.transactions.createIndex("date")
db.budgets.createIndex([("user_id", 1), ("month", 1), ("year", 1)])
```

---

## Future Enhancements

- [ ] Payment integration (Razorpay/Stripe)
- [ ] Export transactions (CSV/PDF)
- [ ] Recurring transactions
- [ ] Investment tracking
- [ ] Multi-currency support
- [ ] Push notifications
- [ ] Analytics dashboard API
- [ ] WebSocket for real-time updates
- [ ] Multi-language support
- [ ] Export to accounting software

---

## License

MIT License - See LICENSE file for details

---

## Contact

**Project Link:** [https://www.finsightfinance.me](https://www.finsightfinance.me)

**API Documentation:** [https://api.finsightfinance.me/api/docs](https://api.finsightfinance.me/api/docs)

**Backend API:** [https://api.finsightfinance.me](https://api.finsightfinance.me)

---

## Acknowledgments

- [Google Gemini AI](https://gemini.google.com/) for AI capabilities
- [Flask](https://flask.palletsprojects.com/) community
- [MongoDB](https://www.mongodb.com/) for database
- [SendGrid](https://sendgrid.com/) for email delivery
- [Vercel](https://vercel.com/) for frontend hosting

---

## Built With Love

FinSight AI - Intelligent Expense Tracking for Everyone

![Built with Flask](https://img.shields.io/badge/Built%20with-Flask-blue?style=flat)
![Deployed on Railway](https://img.shields.io/badge/Deployed%20on-Railway-orange?style=flat)
