# ADR-001: Lifecycle State Machine Enforcement

## Status
Accepted

## Context
Models move through lifecycle stages (DRAFT → VALIDATED → APPROVED → STAGING → PRODUCTION). Some transitions are valid; others are not. For example:
- A DRAFT version can move to VALIDATED or be ARCHIVED, but not directly to PRODUCTION
- An ARCHIVED version cannot transition further
- Invalid transitions could allow unapproved models to reach production

## Decision
Enforce lifecycle transitions at the service layer before any database write operation. Define a `VALID_TRANSITIONS` dictionary mapping each stage to allowed next stages. Raise `ValueError` immediately if an invalid transition is requested.

```python
VALID_TRANSITIONS = {
    DRAFT: [VALIDATED, ARCHIVED],
    VALIDATED: [APPROVED, ARCHIVED, DRAFT],
    APPROVED: [STAGING, ARCHIVED],
    STAGING: [PRODUCTION, ARCHIVED],
    PRODUCTION: [ARCHIVED],
    ARCHIVED: []
}
```

## Alternatives Considered
1. **Database-level constraints:** Foreign key to allowed_transitions table. Too complex; state machine logic belongs in application.
2. **No validation:** Allow any transition; validate in UI. Risk of inconsistent data; API consumers bypass UI.
3. **Event sourcing:** Immutable event log. Overkill for current scope; future consideration.

## Consequences

### Positive
- ✅ Clear, documented transitions
- ✅ Prevents invalid data states
- ✅ Fast feedback to API consumer (HTTP 400, not silent failure)
- ✅ Testable business logic
- ✅ Production versions cannot be deployed unapproved

### Negative
- ⚠️ No bypass mechanism for admin recovery
- ⚠️ If business rules change, code change required (not configurable)
- ⚠️ Circular transitions (DRAFT ↔ VALIDATED) add complexity

## Follow-up Actions
- Add admin override endpoint (future) with audit logging
- Consider config-driven transitions if multi-tenancy added
- Document state machine in architecture diagram
