from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.models.domain import ModelLifecycleStage, DeploymentState


class ModelVersionSchema(BaseModel):
    """Model version response schema."""
    id: int
    model_id: int
    version: str
    lifecycle_stage: ModelLifecycleStage
    artifact_uri: str
    training_data_uri: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[str] = None
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_approved: bool

    class Config:
        from_attributes = True
        protected_namespaces = ()


class ModelVersionCreateRequest(BaseModel):
    """Create model version request."""
    version: str = Field(..., min_length=1, max_length=50)
    artifact_uri: str = Field(..., min_length=1, max_length=1024)
    training_data_uri: Optional[str] = Field(None, max_length=1024)
    metrics: Optional[Dict[str, Any]] = None
    tags: Optional[str] = None


class ModelVersionUpdateRequest(BaseModel):
    """Update model version lifecycle stage."""
    lifecycle_stage: ModelLifecycleStage
    approved_by: Optional[str] = None


class ModelSchema(BaseModel):
    """Model response schema."""
    id: int
    name: str
    description: Optional[str] = None
    owner: str
    framework: str
    algorithm: str
    created_at: datetime
    updated_at: datetime
    versions: List[ModelVersionSchema] = []

    class Config:
        from_attributes = True
        protected_namespaces = ()


class ModelCreateRequest(BaseModel):
    """Create model request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    owner: str = Field(..., min_length=1, max_length=255)
    framework: str = Field(..., min_length=1, max_length=100)
    algorithm: str = Field(..., min_length=1, max_length=255)


class DeploymentMetricsSchema(BaseModel):
    """Deployment metrics response."""
    id: int
    deployment_id: int
    timestamp: datetime
    prediction_latency_ms: Optional[float] = None
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    quality_score: Optional[float] = None
    drift_score: Optional[float] = None
    availability: Optional[float] = None
    last_successful_inference: Optional[datetime] = None
    monitoring_status: str
    created_at: datetime

    class Config:
        from_attributes = True
        protected_namespaces = ()


class DeploymentSchema(BaseModel):
    """Deployment response schema."""
    id: int
    model_id: int
    version_id: int
    environment: str
    state: DeploymentState
    deployment_request_id: str
    error_message: Optional[str] = None
    deployed_by: str
    requested_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_terminal_state: bool

    class Config:
        from_attributes = True
        protected_namespaces = ()


class DeploymentCreateRequest(BaseModel):
    """Create deployment request."""
    model_id: int
    version_id: int
    environment: str = Field(..., min_length=1, max_length=50)
    deployed_by: str = Field(..., min_length=1, max_length=255)
    deployment_request_id: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Unique idempotency key for duplicate request detection"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: str
    timestamp: datetime
    path: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"


class ModelMetricsResponse(BaseModel):
    """Aggregate metrics for a model."""
    model_id: int
    latest_metrics: Optional[DeploymentMetricsSchema] = None
    environment_deployments: Dict[str, DeploymentSchema] = {}
