# ADR-002: Idempotent Deployment Requests

## Status
Accepted

## Context
Deployments are triggered by API requests. If a network timeout occurs after the deployment is created but before the response reaches the client, the client may retry. Without idempotency, this creates duplicate deployments for the same version. This violates Acceptance Scenario 8 (safe duplicate handling).

## Decision
Each deployment request includes a `deployment_request_id` field, a unique identifier provided by the client. Before creating a new deployment, check if one with the same `deployment_request_id` already exists. If found, return the existing deployment; if not, create a new one.

```python
def request_deployment(db, req):
    # Check for existing deployment
    existing = db.query(Deployment).filter(
        Deployment.deployment_request_id == req.deployment_request_id
    ).first()
    if existing:
        return existing  # Idempotent: return existing
    
    # Create new deployment
    deployment = Deployment(...)
    db.add(deployment)
    db.commit()
    return deployment
```

## Alternatives Considered
1. **No idempotency:** Accept duplicate deployments. Violates acceptance criteria.
2. **Database uniqueness alone:** Rely on unique constraint; client retries fail. Bad UX.
3. **Request deduplication middleware:** Generic but not deployment-specific. Harder to test.

## Consequences

### Positive
- ✅ Safe for client retries (network timeout tolerance)
- ✅ Same request ID always produces same result
- ✅ Client controls uniqueness (no server-side state)
- ✅ Testable

### Negative
- ⚠️ Client must generate unique IDs (UUID4 recommended)
- ⚠️ If client loses ID, cannot retry safely (must use new ID)
- ⚠️ Long-term ID storage for old deployments (for audit)

## Follow-up Actions
- Document client ID generation strategy (UUID4 recommended)
- Add database cleanup for old deployment_request_ids (e.g., >1 year old)
- Monitor duplicate requests to detect client issues
