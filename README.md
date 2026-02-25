# FinSight AI Backend

Flask REST API for the FinSight AI expense tracking application.

## Features

### Core Features
- JWT Authentication with access/refresh tokens
- MongoDB for data storage
- Redis for caching and rate limiting
- Celery for background tasks
- SendGrid email integration

### AI Features (v2)
- Gemini AI-powered expense parsing
- Smart transaction categorization
- Monthly spending insights and recommendations

### WhatsApp Bot (v2)
- Add expenses via WhatsApp messages
- Natural language processing with Gemini AI
- View transactions, budgets, summaries
- Budget alerts (80% threshold warning)
- Weekly summary feature
- Delete/edit transactions

### WhatsApp Commands

```
ADD EXPENSES:
"coffee 50" - Quick add
"lunch at cafe 200 rupees" - Natural language
"uber ride 150" - Transportation

VIEW DATA:
/transactions - Recent 5 expenses
/budget - Budget status
/summary - Monthly spending
/compare - vs last month

MANAGE:
/delete <ID> - Remove expense
/edit <ID> amount 500 - Edit

SETTINGS:
/weekly on - Enable weekly summary
/weekly off - Disable
/alert on - Budget alerts
/alert off - Disable alerts

/start - Quick start guide
/help - All commands
```

## Tech Stack

- Python 3.11+
- Flask
- MongoDB
- Redis
- Celery
- Google Gemini AI
- Twilio WhatsApp API

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
MONGO_URI=mongodb://localhost:27017/finsight_db
JWT_SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
BROKER_URL=redis://localhost:6379/0
RESULT_BACKEND=redis://localhost:6379/0

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+14155238886
```

3. Run locally:
```bash
python run.py
```

## Docker Deployment

```bash
docker-compose up -d
```

## API Endpoints

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login
- POST `/api/auth/refresh` - Refresh token
- POST `/api/auth/send-whatsapp-code` - Send WhatsApp verification code
- POST `/api/auth/verify-whatsapp` - Verify WhatsApp number

### Transactions
- GET `/api/transactions` - Get all transactions
- POST `/api/transactions` - Add transaction
- DELETE `/api/transactions/<id>` - Delete transaction

### Budgets
- GET `/api/budgets` - Get all budgets
- POST `/api/budgets` - Create/update budget
- DELETE `/api/budgets/<id>` - Delete budget

### AI
- POST `/api/ai/parse` - Parse expense with AI
- POST `/api/ai/insights` - Get spending insights

### WhatsApp
- POST `/webhook/whatsapp` - Twilio webhook
- GET `/whatsapp/status` - Check WhatsApp status
- GET `/whatsapp/transactions/recent` - Get WhatsApp transactions

## Production Deployment

Deployed on DigitalOcean Droplet with Docker.

- API: https://api.finsightfinance.me
- API Docs: https://api.finsightfinance.me/api/docs

## License

MIT
