# Imara Financial Services MVP - Merchant API

This is the Formative 1 submission for Advanced Python Programming.  
It implements a production-shaped API for merchant onboarding and financing requests with async alerts and performance optimizations.

## Quick Start

### Prerequisites
- Python 3.10+
- Redis (for Celery broker)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/kellynshuti9/advanced-python-imara-kellynshuti9.git
cd advanced-python-imara-kellynshuti9

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Redis (required for Celery)
# On Ubuntu/Debian: sudo service redis-server start
# On macOS: brew services start redis
# On Windows: use WSL or Redis for Windows

# Start Celery worker (in a separate terminal)
celery -A imara worker --loglevel=info

# Start Django server (in another terminal)
python manage.py runserver
```

### Environment Variables

Create a `.env` file in the project root (optional, defaults work for local development):

```text
REDIS_URL=redis://localhost:6379/0
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/merchants/` | Register a new merchant |
| GET | `/api/merchants/` | List all merchants |
| POST | `/api/financing-requests/` | Create financing request (triggers async alert) |
| GET | `/api/financing-requests/` | List all requests (paginated, 5 per page) |
| GET | `/api/financing-requests/<id>/` | Retrieve a single financing request |
| PATCH | `/api/financing-requests/<id>/` | Update a financing request (triggers async alert) |
| PUT | `/api/financing-requests/<id>/` | Full update of a financing request (triggers async alert) |
| GET | `/api/lender/requests/` | Lender-facing feed (paginated, 5 per page) |
| GET | `/swagger/` | Interactive API documentation (Swagger UI) |

### Example Requests

#### Create a merchant

```bash
curl -X POST http://localhost:8000/api/merchants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mama Mboga Store",
    "email": "mama@example.com",
    "phone": "+254712345678",
    "business_type": "retail"
  }'
```

#### Create a financing request

```bash
curl -X POST http://localhost:8000/api/financing-requests/ \
  -H "Content-Type: application/json" \
  -d '{
    "merchant": 1,
    "amount": 50000.00,
    "purpose": "Stock inventory for festive season"
  }'
```

#### Update a financing request (triggers alert)

```bash
curl -X PATCH http://localhost:8000/api/financing-requests/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved"
  }'
```

#### View lender feed (paginated)

```bash
curl "http://localhost:8000/api/lender/requests/?page=1"
```

#### View all financing requests (with pagination)

```bash
curl "http://localhost:8000/api/financing-requests/?page=1"
```

## Async Alert System

When a financing request is **created** (POST) or **updated** (PATCH/PUT), Celery asynchronously:

- Queues the alert task without blocking the HTTP response
- Attempts to log the alert to `alerts.log`
- Automatically retries up to 3 times if logging fails (60-second delay between retries)
- Records success or failure in the log file

**View alert logs:**

```bash
tail -f alerts.log
```

**Sample successful alert log entry:**

```text
Alert processed for financing request 1
```

**Sample failed alert log entry (after retries):**

```text
ALERT FAILED (after 3 retries) for financing request 1: [error details]
```

## Performance Feature: Pagination

The lender-facing financing request feed (`/api/lender/requests/`) uses **page-based pagination** with 5 items per page. This decision directly addresses Peter's requirement for low-bandwidth operation — lenders on unstable mobile data receive smaller, faster payloads.

Configured in `settings.py`:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5
}
```

## Documentation Artifact

Interactive API documentation is available at:

- `/swagger/` - Swagger UI interface
- `/swagger.json` - OpenAPI schema (JSON)

## Project Structure

```text
api/                # Main API application
├── models.py       # Merchant and FinancingRequest (with updated_at field)
├── serializers.py  # Validation logic (amount > 0)
├── views.py        # Endpoint handlers (create, list, update, lender feed)
├── tasks.py        # Celery async tasks (with retry logic)
└── urls.py         # API routes
imara/              # Django project config
├── settings.py     # Pagination, Celery, Redis config
├── celery.py       # Celery app definition
└── urls.py         # Root URL config (includes Swagger)
alerts.log          # Async alert audit trail
db.sqlite3          # SQLite database (development only)
```

## AI Use Annex (Required Disclosure)

**AI tools used:** ChatGPT (OpenAI)

**How they were used:**
- Debugging Celery configuration and Redis connection issues
- Formatting and structuring this README
- Light code review feedback on `views.py` structure
- Improving `tasks.py` with retry logic and error handling (removing `time.sleep(5)`)
- Creating the ADR.md document structure

**What was NOT generated by AI:**
- The ADR reasoning and stakeholder analysis
- The core business logic in `models.py` and `serializers.py`
- The decision to use pagination vs caching
- The API endpoint design and resource boundaries
- Stakeholder mapping (David, Amina, Peter trade-offs)

**Manual changes after AI assistance:**
- Removed AI-suggested code that didn't fit the project context
- Adjusted validation logic to match specific MVP requirements
- Customized error messages for East African merchant context
- Fixed pagination to 5 items (AI suggested 10, but 5 better for low-bandwidth)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'celery'` | Run `pip install -r requirements.txt` |
| Redis connection refused | Start Redis: `redis-server` or `sudo service redis-server start` |
| Alerts not appearing in log | Check Celery worker is running: `celery -A imara worker --loglevel=info` |
| Pagination not working | Verify `REST_FRAMEWORK` settings in `settings.py` |
| Changes not reflected after code update | Restart Celery worker (Ctrl+C, then `celery -A imara worker --loglevel=info`) |
| Migration errors after adding `updated_at` | Run `python manage.py makemigrations` then `python manage.py migrate` |
| `alerts.log` not created | The file auto-creates on first alert; check write permissions |

## Submission Info

- **Branch:** `f1/mvp`
- **Target branch:** `main`
- **Repository:** [advanced-python-imara-kellynshuti9](https://github.com/kellynshuti9/advanced-python-imara-kellynshuti9)

