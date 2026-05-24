# Architecture Decision Record: Imara Financial Services MVP

## Decision
**Use Celery with Redis as the async task queue for background alert processing, combined with DRF pagination for the lender financing request feed.**

## Context
Imara Financial Services MVP requires:
- Non-blocking alert dispatch when financing requests are created
- Reliable performance on low-bandwidth mobile networks (Peter's concern)
- Maintainable resource boundaries (Amina's concern)

## Decision Drivers
- **Peter (Field Operations):** Needs lightweight API responses that work on unstable connections
- **Amina (Tech Lead):** Wants clean separation between request/response and background work
- **David (Product):** Wants visible product progress and rapid onboarding

## What This Decision Improves
| Aspect | Improvement |
|--------|-------------|
| User experience | API returns immediately without waiting for alert processing |
| Network performance | Pagination limits each response to 5 records (configured in settings.py) |
| Maintainability | Alert logic isolated in `tasks.py`, separate from views |
| Developer onboarding | Standard Django + Celery pattern, well-documented |

## What This Decision Makes Harder
| Challenge | Mitigation |
|-----------|-------------|
| Infrastructure complexity | Redis must be running locally and in production |
| Debugging async failures | Alerts logged to `alerts.log` for visibility |
| Idempotency | Alerts may retry; current implementation assumes idempotent logging |

## Stakeholder Benefit Analysis
| Stakeholder | Benefit Level | Reasoning |
|-------------|---------------|-----------|
| Peter (Performance) | High | Pagination reduces payload size; async prevents timeout failures |
| Amina (Maintainability) | High | Clear separation of concerns, easy to extend |
| David (Progress) | Medium | Works now, but needs Redis setup documented |

## Non-Functional Requirements Affected
| NFR | Impact | Status |
|-----|--------|--------|
| Performance | Positive | Pagination limits data transfer; async prevents blocking |
| Reliability | Neutral | Redis becomes a dependency; logs provide audit trail |
| Maintainability | Positive | Modular design with clear boundaries |
| Deployability | Negative | Requires Redis + Celery worker process |

## Status
**Accepted** — suitable for MVP, will revisit if alert volume exceeds 1000/hour.

## Alternatives Considered
1. **Synchronous alerts** → Rejected (violates non-blocking requirement)
2. **Django background tasks without Celery** → Rejected (less reliable, harder to monitor)
3. **No pagination** → Rejected (poor low-bandwidth experience for lenders)