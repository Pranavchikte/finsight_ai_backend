# Finsight AI — Backend

Finsight AI is a full-stack, AI-powered expense manager that automates transaction logging and provides intelligent budgeting advice. This repository contains the high-performance backend powering the product launch. The live frontend is available at: https://finsight-ai-frontend-2grh.vercel.app/

Launch status: Startup product — live (production).

Table of contents
- About
- Live demo
- Key features
- Architecture overview
- Technology stack
- API overview
- Installation & local development
- Environment variables
- Running (dev & production)
- Background tasks & Celery
- Deployment & CI/CD
- Observability & monitoring
- Security best practices
- Contributing
- License
- Contact

About
-------
Finsight AI automates expense tracking by ingesting transactions (bank, card, receipts), using GenAI (Gemini API) to summarize transactions, categorize them, and deliver personalized budgeting recommendations. The backend is built for performance, scale, and rapid iteration.

Key highlights implemented
- Flask-based REST API designed for low latency and ease of extension.
- Celery + Redis for asynchronous/background processing (GenAI calls, heavy transforms, batch imports).
- GenAI core integration (Gemini API) to produce smart transaction summaries and financial insights.
- MongoDB for flexible, schema-evolving data persistence of users, transactions, budgets, and analytics.
- Deployed end-to-end on Railway with CI/CD-enabled pipelines.
- React frontend (separate repo) consumes backend APIs and provides the user interface.

Live demo
---------
Frontend: https://finsight-ai-frontend-2grh.vercel.app/

Features
--------
- Automatic transaction ingestion and parsing
- AI-driven transaction summarization & categorization using Gemini
- Intelligent budget recommendations and insights
- Asynchronous processing for heavy/long-running jobs
- User management & authentication (JWT/Bearer)
- Analytics endpoints for dashboards and reporting

Architecture overview
---------------------
- Client (React) <--> Backend (Flask REST API)
- Backend enqueues heavy tasks to Celery (using Redis broker)
- Celery workers call Gemini API for summarization and insights, then persist results to MongoDB
- MongoDB stores users, transactions, budgets, and analytics
- Deployment: Railway (backend + workers + MongoDB add-on). Redis as a hosted service (or Railway add-on)

Tech stack
----------
- Backend framework: Flask
- Asynchronous tasks: Celery
- Broker: Redis
- AI / GenAI: Gemini API
- Database: MongoDB
- Frontend: React (separate repository)
- Deployment: Railway (CI/CD)
- Language: Python 3.10+

API overview (high-level)
-------------------------
This README documents high-level endpoints. For a full OpenAPI/Swagger spec, check the repo's docs or the /openapi endpoint (if enabled).

- POST /api/v1/auth/register — create user
- POST /api/v1/auth/login — authenticate user, returns JWT
- GET /api/v1/transactions — list user transactions (supports pagination, filters)
- POST /api/v1/transactions/import — upload or submit transactions for ingestion
- POST /api/v1/transactions/:id/summarize — trigger/manual re-summarize by GenAI
- GET /api/v1/insights/summary — aggregated budget insights and recommendations
- POST /api/v1/budgets — create/update budget goals

Installation & local development
-------------------------------
Prerequisites
- Python 3.10+
- pip (or poetry)
- Redis (local or remote)
- MongoDB (local or remote)
- Node.js (for frontend, optional)
- Railway CLI / account (optional for deployment)

Quickstart (development)
1. Clone the repo
   git clone https://github.com/Pranavchikte/finsight_ai_backend.git
   cd finsight_ai_backend

2. Create a virtual environment and install dependencies
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt

3. Create .env (see Environment variables section below) and fill values.

4. Start Redis and MongoDB locally or configure connections to hosted instances.

5. Run the backend (dev server)
   export FLASK_APP=app
   export FLASK_ENV=development
   flask run --host=0.0.0.0 --port=5000

6. Start a Celery worker (in a separate terminal)
   celery -A app.celery_app worker --loglevel=info

7. Optionally run scheduled beat tasks
   celery -A app.celery_app beat --loglevel=info

Environment variables
---------------------
Create a .env file in the project root with the variables below (example values shown). NEVER commit production secrets to source control.

- FLASK_ENV=development
- FLASK_APP=app
- FLASK_DEBUG=true
- SECRET_KEY=super-secret-key
- JWT_SECRET_KEY=jwt-secret-key
- MONGO_URI=mongodb://localhost:27017/finsight
- REDIS_URL=redis://localhost:6379/0
- GEMINI_API_KEY=sk-...
- RAILWAY_ENV=local_or_production
- SENTRY_DSN= (optional; for error tracking)
- CELERY_BROKER_URL=${REDIS_URL}
- CELERY_RESULT_BACKEND=${REDIS_URL}

Running (production)
--------------------
- Use a WSGI server (Gunicorn / uvicorn for ASGI if using async extensions).
- Example Gunicorn command:
  gunicorn -w 4 -b 0.0.0.0:8000 app:app
- Ensure environment variables are set in your production environment (Railway, Docker, or other).
- Run Celery workers and beat processes separately in production.

Background tasks & Celery
-------------------------
- Long-running and I/O-bound operations (Gemini API calls, batch imports, scheduled reconciliations) run as Celery tasks.
- Redis is used as the broker and result backend.
- Tasks are idempotent where practical and include retry/backoff policies for transient failures.
- Celery setup files:
  - app/celery_app.py (Celery factory & config)
  - tasks/genai_tasks.py (Gemini interaction tasks)
  - tasks/import_tasks.py (batch imports)

Deployment & CI/CD
------------------
- We deploy via Railway with environment variables configured in the Railway project.
- CI can run tests, linting, and build steps before deploying.
- Typical pipeline:
  - Run tests (pytest)
  - Run linters (flake8, black)
  - Build/update Docker image (if used)
  - Deploy to Railway / other cloud providers

Observability & monitoring
--------------------------
- Sentry integration available via SENTRY_DSN for error collection.
- Structured logging (JSON format) is recommended for production logs.
- Health endpoints:
  - GET /health — basic service health
  - GET /metrics — Prometheus metrics (if enabled)
- Alerts & dashboards: connect logs/metrics to your monitoring stack (Datadog, Grafana, Railway integrations).

Security best practices
-----------------------
- Keep GEMINI_API_KEY and other secrets in secure secret stores (Railway secrets, environment vault).
- Use HTTPS in production for all endpoints.
- Protect authentication endpoints with rate limiting.
- Ensure minimal permissions for database users.
- Validate and sanitize any user-supplied data before persistence or AI prompt construction.
- Follow principle of least privilege for downstream APIs and accounts.

Testing
-------
- Unit tests: pytest
- Run tests:
  pytest tests/
- Aim to mock external APIs (Gemini, payment services) using vcrpy or unittest.mock for deterministic tests.

Contributing
------------
We welcome contributions. Suggested workflow:
1. Fork the repo.
2. Create a feature branch: git checkout -b feat/my-feature
3. Run tests and linters locally.
4. Create a PR against main with an informative description and linked issue (if applicable).

Please follow these guidelines:
- Write tests for new functionality.
- Keep commits small and focused.
- Document new env vars and endpoints.

License
-------
Specify your project license here (e.g., MIT). Replace this line with the exact license you intend to use.

Contact
-------
- Maintainer: Pranav Chikte 
- Product/Marketing: https://finsight-ai-frontend-2grh.vercel.app/

Acknowledgements
----------------
Built with open source tools and the Gemini API for GenAI capabilities.

What's next / tips for maintainers
---------------------------------
- Add an automated OpenAPI spec generator and host docs (Swagger UI).
- Add more integration tests around Celery tasks and GenAI calling flows.
- Monitor usage of the Gemini API and rate-limit or queue requests to avoid bill shock.
- Add role-based access controls (RBAC) for multi-tenant or enterprise features.

Thank you — 

