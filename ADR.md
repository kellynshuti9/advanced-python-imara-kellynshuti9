# Architecture Decision Records - Imara Financial Services

## ADR-001: Dual Authentication Strategy (Formative 2)

**Status:** Accepted

**Context:** Formative 1 had no authentication. Need to support both API consumers (programmatic access) and human staff (dashboard access).

**Decision:** Implement JWT for API consumers + Session-based authentication for staff dashboard.

**Decision Drivers:**
- API consumers need stateless, scalable authentication
- Staff need ability to logout and revoke sessions
- Compliance requires audit trail of all logins

**Trade-offs:**
| Aspect | JWT | Session |
|--------|-----|---------|
| State | Stateless | Stateful |
| Revocation | Difficult (needs blacklist) | Easy (delete session) |
| Scalability | High | Requires shared storage |
| Use case | API consumers | Staff dashboard |

**Consequences:**
- Two authentication systems to maintain
- JWT tokens valid for 2 hours (cannot revoke)
- Sessions stored in Django's cache/DB

---

## ADR-002: Role-Based Access Control with Object-Level Permissions (Formative 2)

**Status:** Accepted

**Context:** Different user types need different data access levels. Merchants should not see other merchants' data.

**Decision:** 5 roles (merchant, lender_partner, compliance, admin, support) with object-level permissions.

**Roles & Access:**
| Role | Data Access | Operations |
|------|-------------|------------|
| merchant | Own data only | Create requests |
| lender_partner | Assigned merchants | Approve/reject |
| compliance | All data | Read-only + audit |
| admin | All data | Full CRUD |
| support | Basic info | Read-only, no PII |

**Decision Drivers:**
- Compliance requires separation of duties
- Data privacy for merchants
- Audit trail for sensitive access

**Implementation:**
- `get_queryset()` filters list views
- `has_object_permission()` checks detail access
- Centralized permissions in `permissions.py`

**Consequences:**
- More complex permission logic
- Database queries for each permission check
- Clear audit trail of who accessed what

---

## ADR-003: Privacy & Audit Compliance (Formative 2)

**Status:** Accepted

**Context:** Sensitive PII (tax_id, account_number) stored in plaintext. No record of who accessed sensitive data.

**Decision:** Fernet field-level encryption + database-backed audit logging + rate-limited exports.

**Components:**

### Field Encryption
- **Algorithm:** Fernet (symmetric encryption)
- **Fields:** `tax_id`, `account_number`
- **Key storage:** Environment variables

### Audit Logging
- **Actions logged:** LOGIN, LOGOUT, CREATE, UPDATE, DELETE, EXPORT, VIEW_SENSITIVE
- **Data captured:** User, action, resource, IP address, timestamp, user agent
- **Retention:** 500 most recent logs

### Export Controls
- **Rate limit:** 10 requests per hour
- **Restricted to:** Admin and compliance roles
- **Audited:** All exports logged

**Decision Drivers:**
- Regulatory compliance (GDPR, PCI)
- Audit trail for investigations
- Prevent data exfiltration

**Trade-offs:**
| Feature | Benefit | Cost |
|---------|---------|------|
| Encryption | PII protected at rest | +10-15% latency |
| Audit logs | Complete visibility | Storage growth |
| Rate limiting | Prevents exfiltration | Legitimate users throttled |

**Consequences:**
- Cannot search encrypted fields
- Audit logs need rotation policy
- Export throttling may frustrate power users

---

## ADR-004: Async Alerts with Celery + Redis (Formative 1)

**Status:** Accepted (Preserved from Formative 1)

**Context:** Non-blocking alert dispatch when financing requests are created or updated.

**Decision:** Celery with Redis as async task queue.

**Benefits:**
- API returns immediately without waiting
- Retry logic (3 attempts) for reliability
- Alert logging to `alerts.log`

**Limitations:**
- Redis must be running
- Celery worker process required
- Alerts disabled for development (Redis not required)

---

## ADR-005: Pagination for Low-Bandwidth (Formative 1)

**Status:** Accepted (Preserved from Formative 1)

**Context:** Lenders on unstable mobile connections need small payloads.

**Decision:** Page-based pagination with 5 items per page.

**Configuration:**
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5
}
Decision Summary
ADR	Decision	Status
ADR-001	Dual Authentication (JWT + Session)	✅ Accepted
ADR-002	RBAC with Object-Level Permissions	✅ Accepted
ADR-003	Privacy & Audit (Encryption + Logs + Rate Limits)	✅ Accepted
ADR-004	Async Alerts with Celery + Redis	✅ Preserved
ADR-005	Pagination (5 items per page)	✅ Preserved