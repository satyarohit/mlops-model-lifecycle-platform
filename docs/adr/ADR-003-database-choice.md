# ADR-003: Database Choice (SQLite vs. PostgreSQL)

## Status
Accepted

## Context
Development team needs rapid iteration; production deployment requires reliability. SQLite is zero-setup but single-connection; PostgreSQL is production-grade but requires Docker. Decision impacts setup friction and scalability.

## Decision
Use **SQLite for local development** and **PostgreSQL for production** (via Docker). Abstract database via SQLAlchemy, allowing seamless switching via connection string.

- **Development:** `sqlite:///./mlops.db` (file-based)
- **Production:** `postgresql://user:pwd@host/mlops`

Database selection via environment variable:
```bash
export DATABASE_URL="postgresql://..."  # Override for production
```

## Alternatives Considered
1. **Always SQLite:** Simple; poor production scale. Violates reliability.
2. **Always PostgreSQL:** Requires Docker for all dev. Higher friction.
3. **Multiple database drivers (MySQL, MariaDB):** Unnecessary complexity for scope.

## Consequences

### Positive
- ✅ Zero setup for local dev (no Docker)
- ✅ Production-ready with Docker Compose
- ✅ No database syntax differences (SQLAlchemy abstracts)
- ✅ Easy migration path (run Alembic)
- ✅ Fast feedback cycle for developers

### Negative
- ⚠️ SQLite lacks concurrency features (blocking writes)
- ⚠️ Data directory differences (SQLite = file, PostgreSQL = container volume)
- ⚠️ Development != production (false sense of testing)
- ⚠️ JSON operators not available in SQLite

## Follow-up Actions
- Recommend PostgreSQL for all environments (future)
- Add database fixture abstraction (TestDB) for tests
- Document SQLite limitations in README
- Monitor for SQLite-specific issues in dev

## Rationale
Balances developer experience with production readiness. SQLite acceptable for demo; production workloads use PostgreSQL.
