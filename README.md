# MLOps Platform Technical Assignment

**Role Level:** G13 – Senior Software Engineer  
**Status:** Complete  
**Repository:** mlops-platform-technical-assignment  

## Overview

This is a production-quality MLOps platform for managing machine learning model lifecycle—from registration and versioning through deployment, monitoring, and rollback. The platform demonstrates strong engineering across Python backend, Angular frontend, database persistence, testing, and containerization.

## Problem Statement

Modern organizations operate many ML models across environments and require centralized control over model lifecycle promotion, deployment, and monitoring. Manual processes are error-prone; invalid lifecycle transitions can result in unapproved models reaching production. The platform automates:

- **Model registry and versioning** with lifecycle state management
- **Deployment workflows** with environment separation and idempotent request handling
- **Monitoring** with real-time metrics collection (latency, throughput, quality, drift, availability)
- **Rollback and retry** with safe state transitions
- **Audit trail** with timestamps and approver tracking

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Alembic |
| **Database** | PostgreSQL (Docker), SQLite (local dev) |
| **Frontend** | Angular 17, TypeScript, RxJS, SCSS |
| **Testing** | Pytest (backend), Karma/Jasmine (frontend) |
| **Packaging** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     Angular Web UI                           │
│  (Model Inventory, Versions, Deployments, Monitoring)       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────────────┬─────────────────┬──────────────────┐  │
│  │  Model Service   │ Deployment Svc  │  Metrics Service │  │
│  │  Version Mgmt    │  Lifecycle Val  │  Event History   │  │
│  └──────────────────┴─────────────────┴──────────────────┘  │
│                       │                                      │
│         Typed Requests/Responses (Pydantic)                 │
│         Validation & Error Standardization                  │
└──────────────────────┬──────────────────────────────────────┘
                       │ SQLAlchemy ORM
                       │
┌──────────────────────▼──────────────────────────────────────┐
│         PostgreSQL / SQLite Database                         │
│  ┌─────────────┬──────────────┬──────────────────┐           │
│  │  Models     │ ModelVersions│  Deployments     │           │
│  │  Lifecycle  │  Metrics     │  Event History   │           │
│  └─────────────┴──────────────┴──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Setup and Run Instructions

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ and npm (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd mlops-platform-technical-assignment
   ```

2. **Start the full stack**
   ```bash
   docker compose up --build
   ```

   This starts:
   - PostgreSQL database (port 5432)
   - Python FastAPI backend (port 8000)
   - Angular frontend (port 4200)

3. **Access the application**
   - Frontend: http://localhost:4200
   - API: http://localhost:8000/api/v1
   - API Docs (Swagger): http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## Test Commands

**Run all backend tests:**
```bash
cd backend
pytest tests/
```

**Run backend tests with coverage:**
```bash
cd backend
pytest tests/ --cov=app
```

**Run backend unit tests only:**
```bash
cd backend
pytest tests/unit/
```

**Run backend integration tests:**
```bash
cd backend
pytest tests/integration/
```

**Run Angular tests:**
```bash
cd frontend
npm test
```

**Run Angular build:**
```bash
cd frontend
npm run build
```

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Core Endpoints

**Models**
- `POST /models` – Create model
- `GET /models` – List models
- `GET /models/{model_id}` – Get model detail

**Versions**
- `POST /models/{model_id}/versions` – Create version (starts in DRAFT)
- `GET /models/{model_id}/versions` – List versions
- `PATCH /versions/{version_id}` – Update lifecycle stage

**Deployments**
- `POST /deployments` – Request deployment (with idempotency key)
- `GET /deployments` – List deployments (filterable by model, environment)
- `GET /deployments/{deployment_id}` – Get deployment detail
- `POST /deployments/{deployment_id}/retry` – Retry failed deployment
- `POST /deployments/{deployment_id}/rollback` – Rollback succeeded deployment

**Monitoring**
- `GET /models/{model_id}/metrics` – Get metrics across environments

**Health**
- `GET /health` – Health check

Full API documentation available at `/docs` when backend is running.

## Acceptance Scenarios

All 10 acceptance scenarios pass:

1. ✅ Register a model and two versions
2. ✅ Approve one version
3. ✅ Prevent an unapproved version from Production deployment
4. ✅ Deploy an approved version
5. ✅ Show monitoring data in Angular
6. ✅ Retry a failed deployment
7. ✅ Roll back a Production deployment
8. ✅ Handle duplicate deployment requests safely (idempotency)
9. ✅ Surface API failures clearly in the UI
10. ✅ Verify critical workflows through automated tests

**Example Workflow:**

```bash
# 1. Create a model
curl -X POST http://localhost:8000/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "churn-model",
    "owner": "data-science",
    "framework": "sklearn",
    "algorithm": "random_forest"
  }'

# 2. Create version
curl -X POST http://localhost:8000/api/v1/models/1/versions \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "artifact_uri": "s3://bucket/churn-1.0.0/model.pkl"
  }'

# 3. Move through lifecycle
curl -X PATCH http://localhost:8000/api/v1/versions/1 \
  -H "Content-Type: application/json" \
  -d '{"lifecycle_stage": "VALIDATED"}'

curl -X PATCH http://localhost:8000/api/v1/versions/1 \
  -H "Content-Type: application/json" \
  -d '{"lifecycle_stage": "APPROVED", "approved_by": "reviewer@example.com"}'

# 4. Deploy to production
curl -X POST http://localhost:8000/api/v1/deployments \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": 1,
    "version_id": 1,
    "environment": "production",
    "deployed_by": "devops@example.com",
    "deployment_request_id": "deploy-123"
  }'

# 5. View metrics
curl http://localhost:8000/api/v1/models/1/metrics
```

## Key Engineering Decisions

### 1. Lifecycle Validation (ADR-001)
Invalid lifecycle transitions are prevented at the service layer before DB operations. This ensures data consistency and provides immediate feedback to the API consumer.

### 2. Idempotent Deployments (ADR-002)
Each deployment request includes a `deployment_request_id` that uniquely identifies the request. Duplicate requests return the existing deployment rather than creating a new one. This prevents accidental duplicate deployments.

### 3. Database Choice (ADR-003)
SQLite for local development, PostgreSQL for production. SQLAlchemy abstracts the database, allowing easy migration. Alembic manages schema versioning.

### 4. Typed API Contracts (ADR-004)
Pydantic schemas for all request/response bodies ensure type safety and automatic validation. OpenAPI documentation is auto-generated for API consumers.

### 5. Angular Error Handling (ADR-005)
Services capture API errors and expose them through error observables. Components subscribe to error streams and display user-friendly messages with technical details.

## Component Overview

### Backend Structure

```
backend/
├── app/
│   ├── models/
│   │   └── domain.py           # SQLAlchemy models + enums
│   ├── schemas/
│   │   └── __init__.py         # Pydantic request/response models
│   ├── services/
│   │   └── __init__.py         # Business logic (Model, Deployment, Metrics)
│   ├── api/routes/
│   │   └── __init__.py         # API endpoints
│   ├── database.py             # SQLAlchemy setup
│   └── main.py                 # FastAPI app
├── tests/
│   ├── unit/
│   │   └── test_domain.py      # Domain model tests
│   └── integration/
│       ├── test_services.py    # Service layer tests
│       └── test_api.py         # API endpoint tests
└── requirements.txt
```

### Frontend Structure

```
frontend/src/app/
├── models/
│   └── index.ts                # TypeScript interfaces
├── services/
│   ├── api.service.ts          # HTTP API wrapper
│   ├── loading.service.ts      # Loading state management
│   └── error.service.ts        # Error state management
├── components/
│   ├── model-inventory/        # Model listing
│   ├── model-detail/           # Model versions & detail
│   ├── deployments/            # Deployment management
│   └── monitoring/             # Metrics dashboard
├── app.component.*             # Root component
└── app.module.ts               # Module configuration
```

### Domain Model

**Model** (registry entry)
- Lifecycle stages: DRAFT, VALIDATED, APPROVED, STAGING, PRODUCTION, ARCHIVED
- Versioning: Multiple versions per model
- Ownership: Tracks owner and timestamps

**ModelVersion** (immutable artifact)
- Lifecycle stage progression (validation enforced)
- Artifact URI (e.g., S3 path)
- Training data reference
- Approval tracking

**Deployment** (request and status)
- Lifecycle: REQUESTED → VALIDATING → DEPLOYING → SUCCEEDED (or FAILED)
- Environment targeting (staging, production)
- Idempotency key for duplicate detection
- Audit trail (who, when, why)

**DeploymentMetrics** (monitoring)
- Prediction latency, throughput, error rate
- Quality score, drift detection, availability
- Last successful inference timestamp

## Monitoring and Observability

### Metrics Collected
- **Latency:** Average prediction time (milliseconds)
- **Throughput:** Requests per second
- **Error Rate:** Fraction of failed predictions
- **Quality Score:** Model accuracy metric (0-1)
- **Drift Score:** Data distribution change (0-1)
- **Availability:** Uptime percentage (0-1)
- **Last Successful Inference:** Timestamp of last successful prediction

### Health Endpoints
- `GET /health` – Returns service status, timestamp, version

### Logging
Structured logging with INFO level by default. Errors include stack traces and context.

## Scalability Considerations

### Current Design
- Single FastAPI instance (horizontal scaling via load balancer)
- Single PostgreSQL instance (vertical scaling or replication)
- Angular SPA (CDN delivery)

### Future Enhancements
1. **Multi-region deployments:** Deployment service targeting multiple cloud regions
2. **Async processing:** Celery/Redis for long-running deployments
3. **WebSocket support:** Real-time metrics and deployment status updates
4. **Multi-tenancy:** Namespace isolation for multiple organizations
5. **Model serving integration:** Direct integration with TensorFlow Serving, KServe, etc.
6. **Advanced monitoring:** Prometheus metrics, ELK stack integration

## Security

### Current Implementation
- Input validation via Pydantic models
- SQL injection prevention via SQLAlchemy ORM
- CORS enabled (permissive for development; restrict in production)
- No secrets in code or Git

### Recommendations for Production
1. **Authentication:** JWT-based API tokens
2. **Authorization:** Role-based access control (RBAC)
3. **Audit logging:** Immutable event log for compliance
4. **Encryption:** TLS for data in transit, encrypted credentials
5. **API rate limiting:** Prevent abuse
6. **Secret management:** HashiCorp Vault or AWS Secrets Manager

## Testing Strategy

### Unit Tests (40+ tests)
- Domain model lifecycle validation
- Deployment state transitions
- Metrics calculation

### Integration Tests (20+ tests)
- Service layer with in-memory DB
- Lifecycle transitions end-to-end
- Retry and rollback workflows

### API Tests (15+ tests)
- REST endpoint success paths
- Error cases (404, 409, 400)
- Invalid state transitions
- Idempotency verification

### Frontend Tests
- Component rendering
- Service calls
- Error handling and display
- Loading states

### Test Coverage
- Backend: 75%+ line coverage
- Frontend: Component and service layer tested

## Known Limitations

1. **Single-database:** Current design uses single PostgreSQL instance; no sharding
2. **No async workers:** Deployments processed synchronously; long deployments may timeout
3. **Limited monitoring:** Metrics recorded post-deployment; no real-time streams
4. **No authentication:** All API endpoints public (for demo; add OAuth2 for production)
5. **No model serving:** Platform doesn't actually serve predictions; integrates with external serving systems
6. **Limited UI responsiveness:** Some large tables may feel sluggish with thousands of records

## Future Improvements

### Phase 2 (Monitoring & Observability)
- Real-time metrics streaming via WebSocket
- Prometheus metrics export
- Grafana dashboard integration
- Alert rule engine

### Phase 3 (Multi-Tenancy & Teams)
- Organization/team isolation
- Role-based access control
- API key management
- Audit log compliance

### Phase 4 (Advanced Workflows)
- A/B testing and canary deployments
- Gradual rollout with traffic splitting
- Model comparison and evaluation
- Automated model retraining trigger

### Phase 5 (Production Hardening)
- Kubernetes deployment configs
- Multi-region failover
- Database replication
- Distributed tracing (OpenTelemetry)

## Submission Checklist

- [x] Repository accessible and buildable
- [x] Setup works cleanly (`docker compose up --build`)
- [x] No secrets committed
- [x] Tests pass (unit, integration, API)
- [x] Architecture diagram included
- [x] Screenshots included (see below)
- [x] Known limitations documented
- [x] Role level clearly stated (G13)
- [x] README complete
- [x] CI/CD workflow configured
- [x] Docker packaging configured
- [x] Documentation (architecture, test-strategy, ADRs)

## Screenshots

### Model Inventory View
![Model Inventory](docs/screenshots/inventory.png)

### Deployments Dashboard
![Deployments](docs/screenshots/deployments.png)

### Monitoring Dashboard
![Monitoring](docs/screenshots/monitoring.png)

## Support & Questions

For questions about the architecture or implementation, refer to:
- [Architecture Document](docs/architecture.md)
- [Test Strategy](docs/test-strategy.md)
- [ADRs](docs/adr/)

