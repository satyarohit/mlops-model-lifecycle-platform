from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.schemas import (
    ModelSchema,
    ModelCreateRequest,
    ModelVersionSchema,
    ModelVersionCreateRequest,
    ModelVersionUpdateRequest,
    DeploymentSchema,
    DeploymentCreateRequest,
    ModelMetricsResponse,
    DeploymentMetricsSchema,
    ErrorResponse,
)
from app.services import (
    ModelService,
    ModelVersionService,
    DeploymentService,
    MetricsService,
)

router = APIRouter(prefix="/api/v1", tags=["mlops"])


# Model endpoints
@router.post("/models", response_model=ModelSchema, status_code=status.HTTP_201_CREATED)
def create_model(req: ModelCreateRequest, db: Session = Depends(get_db)):
    """Create a new model."""
    try:
        model = ModelService.create_model(db, req)
        return model
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/models", response_model=List[ModelSchema])
def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all models."""
    return ModelService.list_models(db, skip, limit)


@router.get("/models/{model_id}", response_model=ModelSchema)
def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get model by ID."""
    model = ModelService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return model


# Model version endpoints
@router.post("/models/{model_id}/versions", response_model=ModelVersionSchema, status_code=status.HTTP_201_CREATED)
def create_version(model_id: int, req: ModelVersionCreateRequest, db: Session = Depends(get_db)):
    """Create a new model version."""
    try:
        version = ModelVersionService.create_version(db, model_id, req)
        return version
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/models/{model_id}/versions", response_model=List[ModelVersionSchema])
def list_versions(model_id: int, db: Session = Depends(get_db)):
    """List all versions for a model."""
    model = ModelService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return ModelVersionService.list_versions(db, model_id)


@router.patch("/versions/{version_id}", response_model=ModelVersionSchema)
def update_version_lifecycle(
    version_id: int,
    req: ModelVersionUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update model version lifecycle stage."""
    try:
        version = ModelVersionService.update_lifecycle_stage(
            db, version_id, req.lifecycle_stage, req.approved_by
        )
        return version
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Deployment endpoints
@router.post("/deployments", response_model=DeploymentSchema, status_code=status.HTTP_201_CREATED)
def request_deployment(req: DeploymentCreateRequest, db: Session = Depends(get_db)):
    """Request a deployment."""
    try:
        deployment = DeploymentService.request_deployment(db, req)
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/deployments", response_model=List[DeploymentSchema])
def list_deployments(
    model_id: int = None,
    environment: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List deployments with optional filters."""
    return DeploymentService.list_deployments(db, model_id, environment, skip, limit)


@router.get("/deployments/{deployment_id}", response_model=DeploymentSchema)
def get_deployment(deployment_id: int, db: Session = Depends(get_db)):
    """Get deployment by ID."""
    deployment = DeploymentService.get_deployment(db, deployment_id)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found")
    return deployment


@router.post("/deployments/{deployment_id}/retry", response_model=DeploymentSchema)
def retry_deployment(deployment_id: int, db: Session = Depends(get_db)):
    """Retry a failed deployment."""
    try:
        deployment = DeploymentService.retry_deployment(db, deployment_id)
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/deployments/{deployment_id}/rollback", response_model=DeploymentSchema)
def rollback_deployment(deployment_id: int, db: Session = Depends(get_db)):
    """Rollback a succeeded deployment."""
    try:
        deployment = DeploymentService.rollback_deployment(db, deployment_id)
        return deployment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Metrics endpoint
@router.get("/models/{model_id}/metrics", response_model=ModelMetricsResponse)
def get_model_metrics(model_id: int, db: Session = Depends(get_db)):
    """Get metrics for a model across all environments."""
    model = ModelService.get_model(db, model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    deployments = DeploymentService.list_deployments(db, model_id=model_id)
    env_deployments = {}

    for deployment in deployments:
        env_key = deployment.environment
        if env_key not in env_deployments or deployment.updated_at > env_deployments[env_key].updated_at:
            env_deployments[env_key] = deployment

    latest_metrics = None
    if deployments:
        latest_deployment = max(deployments, key=lambda d: d.updated_at)
        latest_metrics = MetricsService.get_latest_metrics(db, latest_deployment.id)

    return ModelMetricsResponse(
        model_id=model_id,
        latest_metrics=latest_metrics,
        environment_deployments=env_deployments,
    )


# Health endpoint
@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
