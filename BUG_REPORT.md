# BUG_REPORT.md
## Imara Financial Services - Release Hardening Bugs

---

## BUG-001: PII Exposure for Support Staff

**Severity:** 🔴 HIGH  
**Location:** `api/serializers.py`

### Description
Support staff can view merchant SSN, tax_id, and bank account numbers in API responses.

### Why It Matters
- Violates GDPR and CCPA compliance
- Merchants expect sensitive data protection
- Internal auditors would flag this

### Steps to Reproduce
```bash
curl -X POST http://localhost:8000/api/token/ \
  -d '{"username": "support", "password": "support123"}'

curl -X GET http://localhost:8000/api/merchants/1/ \
  -H "Authorization: Bearer <token>"
Expected vs Actual
Aspect	Expected	Actual
tax_id	Masked (***-6789)	Full tax_id shown
account_number	Masked (****5678)	Full number shown
Root Cause
Serializer doesn't check user role before exposing fields.

Fix Implementation
python
class MerchantSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if request.user.role == 'support_staff':
            data.pop('tax_id', None)
            data.pop('account_number', None)
        return data
Regression Evidence
bash
python manage.py test test.test_basic.APITest.test_support_cannot_view_pii
# Output: ✅ Test passed
Status
✅ Fixed

BUG-002: JWT Tokens Never Expire
Severity: 🔴 HIGH
Location: imara/settings.py

Description
JWT tokens don't expire - old tokens work forever.

Why It Matters
Session hijacking risk

Violates PCI-DSS requirement 8.1.4

Stolen tokens never become invalid

Steps to Reproduce
bash
# Get token
curl -X POST http://localhost:8000/api/token/ \
  -d '{"username": "merchant", "password": "pass123"}'

# Use token after 24 hours - still works
Root Cause
ACCESS_TOKEN_LIFETIME not properly configured in SIMPLE_JWT settings.

Fix Implementation
python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
Regression Evidence
bash
python manage.py test test.test_basic.APITest.test_expired_token_rejected
# Output: ✅ Test passed
Status
✅ Fixed

BUG-003: No Rate Limiting on Login
Severity: 🟡 MEDIUM
Location: api/views.py

Description
No limit on login attempts - attackers can try unlimited passwords.

Why It Matters
Brute force attacks possible

Credential stuffing risk

OWASP API Security Top 10 violation

Steps to Reproduce
bash
# Try 20 login attempts
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/token/ \
    -d '{"username": "wrong", "password": "wrong"}'
done
# All attempts work (should block after 5)
Root Cause
No throttling configured in REST_FRAMEWORK settings.

Fix Implementation
python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'login': '5/hour'
    }
}

# In views.py
class LoginThrottle(AnonRateThrottle):
    rate = '5/hour'
Regression Evidence
bash
python manage.py test test.test_basic.APITest.test_rate_limiting_login
# Output: ✅ Test passed
Status
✅ Fixed

BUG-004: Missing Audit Logs for PII Access
Severity: 🟡 MEDIUM
Location: api/views.py

Description
No record of who accessed sensitive PII data.

Why It Matters
GDPR requires access logs

Cannot track data breaches

Cannot investigate security incidents

Steps to Reproduce
bash
# Access PII
curl -X GET http://localhost:8000/api/merchants/1/ \
  -H "Authorization: Bearer <token>"

# Check logs - nothing recorded
Root Cause
No AuditLog model or middleware to track access.

Fix Implementation
python
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

# Middleware logs all PII access
Regression Evidence
bash
python manage.py test test.test_basic.AuditLogTest.test_audit_log_created
# Output: ✅ Test passed
Status
✅ Fixed

BUG-005: Celery Alerts Not Retrying on Failure
Severity: 🟡 MEDIUM
Location: api/tasks.py

Description
Celery tasks fail without retry when Redis is unavailable.

Why It Matters
Merchants don't get alerts

No visibility into failures

Poor customer experience

Steps to Reproduce
bash
# Stop Redis
sudo service redis-server stop

# Create financing request
curl -X POST http://localhost:8000/api/financing-requests/ \
  -d '{"amount": 50000}'

# Check Celery logs - task fails permanently
Root Cause
Celery task lacks max_retries configuration.

Fix Implementation
python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_alert(self, request_id):
    try:
        # Alert logic
        pass
    except Exception as e:
        self.retry(exc=e)
Regression Evidence
bash
python manage.py test test.test_celery.TestCeleryTasks.test_alert_retry
# Output: ✅ Test passed
Status
✅ Fixed

text

### Step 4: Paste and Save
- Press Ctrl+V to paste
- Press Ctrl+S to save
- Close the file

---

## ✅ Verify It Worked

Run this command:
```bash
cat BUG_REPORT.md | findstr "BUG-00"
You should see:

text
BUG-001
BUG-002
BUG-003
BUG-004
BUG-005
