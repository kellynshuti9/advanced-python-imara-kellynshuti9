# Imara Financial Services API

**Formative 1: MVP** | **Formative 2: Compliance Retrofit** | 

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

## Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| Redis | 6.0+ (for Celery alerts) |
| Git | Any |

### Installation

```bash
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
# Windows: download Redis
# Mac: brew install redis && brew services start redis
# Linux: sudo service redis-server start

# Start Celery worker (separate terminal)
celery -A imara worker --loglevel=info

# Start Django server (another terminal)
python manage.py runserver
Environment Variables
Create .env file:

env
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ENCRYPTION_KEY=your-fernet-key
REDIS_URL=redis://localhost:6379/0
Generate encryption key:

bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
API Endpoints (Complete)
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
Compliance
Method	Endpoint	Description	Auth
GET	/api/audit-logs/	View audit logs	JWT (compliance/admin)
GET	/api/export/	Export data (10/hour)	JWT (admin/compliance)
GET	/api/dashboard/stats/	Dashboard stats	JWT
GET	/api/lender/requests/	Lender view (paginated)	JWT
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
Project Structure
text
api/
├── models.py          # User, Merchant, FinancingRequest, AuditLog
├── serializers.py     # Validation, role-based visibility, encryption
├── views.py           # JWT, Session, RBAC, export controls
├── permissions.py     # RoleBasedPermission, IsMerchantOwner
├── encryption.py      # Fernet encryption utilities
├── tasks.py           # Celery async alerts
└── urls.py            # API routes

imara/
├── settings.py        # DRF, JWT, Celery, pagination config
├── urls.py            # Root URLs with Swagger
└── celery.py          # Celery app definition

alerts.log             # Async alert audit trail
db.sqlite3             # SQLite database
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
Documentation
Document	Content
DECISION_LOG.md	Trade-off analysis for design decisions
API.md	Complete API reference
ADR.md	Architecture Decision Records
Submission Information
Item	Value
Formative 1 Branch	f1/mvp
Formative 2 Branch	f2/compliance-retrofit
Target Branch	main
Repository	advanced-python-imara-kellynshuti9