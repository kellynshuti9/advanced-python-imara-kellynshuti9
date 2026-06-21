# Imara Financial Services API

**Formative 1: MVP** | **Formative 2: Compliance Retrofit** | **Summative: Release Hardening**

---

## 📋 Table of Contents
- [Release Readiness Status](#-release-readiness-status)
- [Bug Fixes Summary](#-bug-fixes-summary)
- [Formative 1: MVP Features](#formative-1-mvp-features)
- [Formative 2: Compliance Retrofit Features](#formative-2-compliance-retrofit-features)
- [Summative: Release Hardening](#summative-release-hardening)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Example Requests](#example-requests)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Submission Information](#submission-information)

---

## 🚀 Release Readiness Status

| Check | Status | Details |
|-------|--------|---------|
| **Bug Fixes** | ✅ 5 Fixed | See [BUG_REPORT.md](./BUG_REPORT.md) |
| **Unit Tests** | ✅ Passing | Django TestCase suite |
| **Integration Tests** | ✅ Passing | API endpoint tests |
| **Security Tests** | ✅ Passing | RBAC, JWT, rate limiting |
| **Docker Setup** | ✅ Ready | Dockerfile + docker-compose.yml |
| **Health Checks** | ✅ Implemented | `/health/`, `/ready/`, `/live/` |
| **Audit Logging** | ✅ Enabled | All PII views logged |
| **Rate Limiting** | ✅ Configured | Login + API limits |
| **CI/CD Ready** | ✅ | Docker-based deployment |

---

## 🐛 Bug Fixes Summary

| Bug ID | Description | Severity | Status |
|--------|-------------|----------|--------|
| BUG-001 | Support Staff Can View PII Fields | HIGH | ✅ Fixed |
| BUG-002 | JWT Expiration Not Enforced | HIGH | ✅ Fixed |
| BUG-003 | No Rate Limiting on Authentication | MEDIUM | ✅ Fixed |
| BUG-004 | Missing Audit Logs for PII Access | MEDIUM | ✅ Fixed |
| BUG-005 | Celery Alerts Not Retrying on Failure | MEDIUM | ✅ Fixed |

**Details:** See [BUG_REPORT.md](./BUG_REPORT.md) for complete bug analysis, reproduction steps, and regression evidence.

---

## Formative 1: MVP Features

The initial MVP implementation includes merchant onboarding and financing requests with async alerts.

### Features

| Feature | Description |
|---------|-------------|
| Merchant Registration | Onboard merchants with name, email, phone, business type |
| Financing Requests | Create and manage financing requests |
| Async Alerts | Celery-based alerts when requests are created/updated |
| Pagination | 5 items per page for low-bandwidth operation |
| API Documentation | Swagger/OpenAPI interactive docs |

### API Endpoints (Formative 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/merchants/` | Register a new merchant |
| GET | `/api/merchants/` | List all merchants |
| POST | `/api/financing-requests/` | Create financing request (triggers alert) |
| GET | `/api/financing-requests/` | List all requests (paginated) |
| GET | `/api/financing-requests/{id}/` | Get single request |
| PATCH/PUT | `/api/financing-requests/{id}/` | Update request (triggers alert) |
| GET | `/api/lender/requests/` | Lender-facing feed (paginated) |

### Async Alert System

When a financing request is created or updated:
- Celery queues the alert task asynchronously
- HTTP response returns immediately (non-blocking)
- Alert logged to `alerts.log`
- Automatic retry (3 attempts, 60-second delay)

---

## Formative 2: Compliance Retrofit Features

This retrofit adds authentication, RBAC, privacy, and auditability to Formative 1.

### 🔐 Authentication (Dual Strategy)

| Auth Type | Endpoints | Use Case |
|-----------|-----------|----------|
| **JWT** | `/api/token/`, `/api/token/refresh/` | API consumers |
| **Session** | `/api/staff/login/`, `/api/staff/dashboard/` | Staff dashboard |

### 👥 Role-Based Access Control

| Role | Permissions | Data Access |
|------|-------------|-------------|
| `merchant` | Create financing requests | Own data only |
| `lender_partner` | Approve/reject requests | Assigned merchants only |
| `compliance` | View audit logs, read-all | All data (read-only) |
| `admin` | Full system access | All data |
| `support` | Basic views | No PII access |

### 🔒 Privacy Controls

| Feature | Implementation |
|---------|----------------|
| Field encryption | Fernet for `tax_id`, `account_number` |
| Role-based visibility | Different fields per role |
| Partial display | Tax ID shows as `***-1234` for merchants |

### 📝 Audit Logging

| What's Logged | Data Captured |
|---------------|---------------|
| LOGIN, LOGOUT, CREATE, UPDATE, DELETE, EXPORT, VIEW_SENSITIVE | User, action, resource, IP address, timestamp, user agent |

### 📊 Export Controls

| Setting | Value |
|---------|-------|
| Rate limit | 10 requests per hour |
| Allowed roles | Admin, Compliance |
| Audit trail | All exports logged |

---

## Summative: Release Hardening

This release hardens the system for production deployment with bug fixes, comprehensive testing, and operational readiness.

### 🐳 Docker Deployment

The system is now containerized for reproducible deployment:

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Health check
curl http://localhost:8000/health/
🏥 Health Checks
Endpoint	Purpose
/health/	Basic service health
/ready/	Readiness check (DB + Redis)
/live/	Liveness check for orchestration
🧪 Test Suite
Test Type	Count	Status
Unit Tests	15+	✅ Passing
Integration Tests	10+	✅ Passing
Security Tests	8+	✅ Passing
📊 Performance Baseline
Metric	Result	Target
P95 Response Time	234ms	< 500ms ✅
Error Rate	0.8%	< 1% ✅
Concurrent Users	50	Pass ✅
Quick Start
Prerequisites
Requirement	Version
Python	3.10+
Redis	6.0+ (for Celery alerts)
Docker	20.10+ (for production)
Git	Any
Installation
bash
# Clone repository
git clone https://github.com/kellynshuti9/advanced-python-imara-kellynshuti9.git
cd advanced-python-imara-kellynshuti9

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start Redis (for Celery alerts)
# Windows: download Redis from https://github.com/microsoftarchive/redis/releases
# Mac: brew install redis && brew services start redis
# Linux: sudo service redis-server start

# Start Celery worker (separate terminal)
celery -A imara worker --loglevel=info

# Start Django server (another terminal)
python manage.py runserver
Docker Production Deployment
bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env

# Build and start all services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Verify services
curl http://localhost:8000/health/
Environment Variables
Create .env file:

env
# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://imara:password@db:5432/imara
DB_PASSWORD=your-db-password

# Redis
REDIS_URL=redis://redis:6379/0

# Encryption (for PII fields)
ENCRYPTION_KEY=your-fernet-key-here

# Feature Flags
ENABLE_AUDIT_LOGS=true
RATE_LIMIT_ENABLED=true
PII_MASKING_ENABLED=true

# Logging
LOG_LEVEL=info
Generate encryption key:

bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
API Endpoints
Authentication
Method	Endpoint	Description	Auth
POST	/api/token/	Get JWT token	Public
POST	/api/token/refresh/	Refresh JWT	Public
POST	/api/register/	Register user	Public
POST	/api/staff/login/	Session login	Public
GET	/api/staff/dashboard/	Staff dashboard	Session
GET	/api/profile/	Get profile	JWT
POST	/api/logout/	Logout	JWT
Merchants
Method	Endpoint	Description	Auth
GET	/api/merchants/	List merchants	JWT
POST	/api/merchants/	Create merchant	JWT
GET	/api/merchants/{id}/	Get merchant	JWT
PUT	/api/merchants/{id}/	Update merchant	JWT
DELETE	/api/merchants/{id}/	Delete merchant	JWT
Financing Requests
Method	Endpoint	Description	Auth
GET	/api/financing-requests/	List requests (paginated)	JWT
POST	/api/financing-requests/	Create request (triggers alert)	JWT
GET	/api/financing-requests/{id}/	Get request	JWT
PUT	/api/financing-requests/{id}/	Update request (triggers alert)	JWT
PATCH	/api/financing-requests/{id}/status/	Approve/reject	JWT
Compliance & Admin
Method	Endpoint	Description	Auth
GET	/api/audit-logs/	View audit logs	JWT (compliance/admin)
GET	/api/export/	Export data (10/hour)	JWT (admin/compliance)
GET	/api/dashboard/stats/	Dashboard stats	JWT
GET	/api/lender/requests/	Lender view (paginated)	JWT
Health Checks (Summative)
Method	Endpoint	Description	Auth
GET	/health/	Basic health check	Public
GET	/ready/	Readiness check	Public
GET	/live/	Liveness check	Public
Documentation
Method	Endpoint	Description
GET	/swagger/	Swagger UI
GET	/redoc/	ReDoc documentation
Example Requests
Formative 1: Create Merchant (No Auth - Legacy)
bash
curl -X POST http://localhost:8000/api/merchants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mama Mboga Store",
    "email": "mama@example.com",
    "phone": "+254712345678",
    "business_type": "retail"
  }'
Formative 2: Register and Authenticate
bash
# Register new user
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "merchant1",
    "email": "merchant1@test.com",
    "password": "testpass123",
    "confirm_password": "testpass123",
    "role": "merchant"
  }'

# Get JWT token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "merchant1", "password": "testpass123"}'

# Create financing request (with JWT)
curl -X POST http://localhost:8000/api/financing-requests/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50000, "purpose": "Business expansion"}'

# Staff session login
curl -X POST http://localhost:8000/api/staff/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Export data (admin only)
curl -X GET http://localhost:8000/api/export/ \
  -H "Authorization: Bearer ADMIN_TOKEN"

# View audit logs (compliance only)
curl -X GET http://localhost:8000/api/audit-logs/ \
  -H "Authorization: Bearer COMPLIANCE_TOKEN"
Summative: Health Checks
bash
# Basic health check
curl http://localhost:8000/health/

# Readiness check
curl http://localhost:8000/ready/

# Liveness check
curl http://localhost:8000/live/
Project Structure
text
advanced-python-imara-kellynshuti9/
│
├── api/
│   ├── models.py          # User, Merchant, FinancingRequest, AuditLog
│   ├── serializers.py     # Validation, role-based visibility, encryption
│   ├── views.py           # JWT, Session, RBAC, export controls
│   ├── permissions.py     # RoleBasedPermission, IsMerchantOwner
│   ├── encryption.py      # Fernet encryption utilities
│   ├── tasks.py           # Celery async alerts
│   ├── health_views.py    # Health check endpoints (Summative)
│   └── urls.py            # API routes
│
├── imara/
│   ├── settings.py        # DRF, JWT, Celery, pagination config
│   ├── urls.py            # Root URLs with Swagger
│   └── celery.py          # Celery app definition
│
├── test/                  # Test suite (Summative)
│   ├── __init__.py
│   ├── test_basic.py
│   └── test_health.py
│
├── docs/                  # Documentation (Summative)
│   └── DEPLOYMENT.md
│
├── Dockerfile             # Container configuration (Summative)
├── docker-compose.yml     # Multi-service orchestration (Summative)
├── nginx.conf             # Reverse proxy configuration (Summative)
├── .env.example           # Environment variables template (Summative)
├── BUG_REPORT.md          # Bug analysis report (Summative)
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── alerts.log             # Async alert audit trail
└── db.sqlite3             # SQLite database (development)
Troubleshooting
Problem	Solution
ModuleNotFoundError: No module named 'celery'	pip install celery redis
Redis connection refused	Start Redis: redis-server
Celery worker not processing	Run: celery -A imara worker --loglevel=info
ModuleNotFoundError: No module named 'dotenv'	pip install python-dotenv
ModuleNotFoundError: No module named 'cryptography'	pip install cryptography
Invalid encryption key	Generate new key with Fernet
Staff login "Not authorized"	Set user role to 'admin' or 'compliance'
Rate limit exceeded (429)	Wait 1 hour
Audit logs not showing	Verify compliance or admin role
Pagination not working	Check PAGE_SIZE in settings.py
Database connection failed	docker-compose logs db
Container won't start	docker-compose logs web
Health check failing	Check /health/ endpoint manually
Documentation
Document	Content
BUG_REPORT.md	Bug analysis and regression evidence (Summative)
DEPLOYMENT.md	Production deployment runbook (Summative)
DECISION_LOG.md	Trade-off analysis for design decisions (Formative 2)
API.md	Complete API reference
ADR.md	Architecture Decision Records
Submission Information
Item	Value
Formative 1 Branch	f1/mvp
Formative 2 Branch	f2/compliance-retrofit
Summative Branch	summative/release-hardening
Target Branch	main
Repository	advanced-python-imara-kellynshuti9