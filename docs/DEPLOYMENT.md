echo @"
# Deployment Guide

## Quick Start

### Local Development
\`\`\`bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
\`\`\`

### Docker Deployment
\`\`\`bash
docker-compose up -d
docker-compose exec web python manage.py migrate
\`\`\`

### Health Checks
- \`/health/\` - Basic health check
- \`/ready/\` - Readiness check (DB + Redis)
- \`/live/\` - Liveness check

### Environment Variables
| Variable | Description |
|----------|-------------|
| DJANGO_SECRET_KEY | Django secret key |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| ENCRYPTION_KEY | Fernet encryption key |
"@ > docs\DEPLOYMENT.md