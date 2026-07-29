# ADR-004: Typed API Contracts with Pydantic

## Status
Accepted

## Context
API consumer and provider must agree on request/response structure. Python's dynamic typing allows any dict to be accepted, risking runtime errors. Manual validation is error-prone. OpenAPI documentation is valuable for client SDKs and testing.

## Decision
Use Pydantic models for all request/response types. Each endpoint declares expected input/output structure, automatic validation, and type hints.

```python
class DeploymentCreateRequest(BaseModel):
    model_id: int
    version_id: int
    environment: str = Field(..., min_length=1, max_length=50)
    deployment_request_id: str = Field(..., min_length=1)

@router.post("/deployments")
def request_deployment(req: DeploymentCreateRequest, db: Session = ...):
    # req is validated; fields are typed
    return DeploymentService.request_deployment(db, req)
```

## Alternatives Considered
1. **Dict acceptance:** Accept any JSON; validate in handler. Messy.
2. **Manual validation:** Write validation code per endpoint. Repeatable.
3. **GraphQL:** Strongly typed; overkill for REST API at this scope.

## Consequences

### Positive
- ✅ Automatic validation (400 response on invalid input)
- ✅ Type hints for IDE autocomplete
- ✅ OpenAPI documentation auto-generated
- ✅ Swagger UI for testing
- ✅ Field constraints (min_length, regex) enforced
- ✅ Clear contract between client and server

### Negative
- ⚠️ Pydantic dependency (external package)
- ⚠️ Learning curve for developers unfamiliar with Pydantic
- ⚠️ Verbose for large schemas (can extract to separate files)

## Follow-up Actions
- Extract large schemas into dedicated modules (app/schemas/models.py, etc.)
- Add examples to schema docstrings
- Generate TypeScript types from Pydantic schemas (future automation)
