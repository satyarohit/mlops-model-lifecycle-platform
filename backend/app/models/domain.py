from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ModelLifecycleStage(str, Enum):
    """Model lifecycle stages."""
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


class DeploymentState(str, Enum):
    """Deployment state transitions."""
    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    DEPLOYING = "DEPLOYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class Model(Base):
    """Model registry entity."""
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner = Column(String(255), nullable=False)
    framework = Column(String(100), nullable=False)  # e.g., "tensorflow", "pytorch"
    algorithm = Column(String(255), nullable=False)  # e.g., "random_forest"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    versions = relationship("ModelVersion", back_populates="model", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="model", cascade="all, delete-orphan")


class ModelVersion(Base):
    """Model version with lifecycle stage."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)  # e.g., "1.0.0"
    lifecycle_stage = Column(String(50), default=ModelLifecycleStage.DRAFT, nullable=False)
    artifact_uri = Column(String(1024), nullable=False)  # Path to model artifact
    training_data_uri = Column(String(1024), nullable=True)
    metrics = Column(Text, nullable=True)  # JSON blob with training metrics
    tags = Column(Text, nullable=True)  # Comma-separated or JSON
    approved_by = Column(String(255), nullable=True)
    approval_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    model = relationship("Model", back_populates="versions")
    deployments = relationship("Deployment", back_populates="version")

    @property
    def is_approved(self) -> bool:
        """Check if version is approved."""
        return self.lifecycle_stage in (
            ModelLifecycleStage.APPROVED,
            ModelLifecycleStage.STAGING,
            ModelLifecycleStage.PRODUCTION,
        )


class Deployment(Base):
    """Deployment request and tracking."""
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey("model_versions.id"), nullable=False, index=True)
    environment = Column(String(50), nullable=False)  # e.g., "staging", "production"
    state = Column(String(50), default=DeploymentState.REQUESTED, nullable=False)
    deployment_request_id = Column(String(255), nullable=False, unique=True, index=True)  # Idempotency key
    error_message = Column(Text, nullable=True)
    deployed_by = Column(String(255), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    model = relationship("Model", back_populates="deployments")
    version = relationship("ModelVersion", back_populates="deployments")

    @property
    def is_terminal_state(self) -> bool:
        """Check if deployment is in a terminal state."""
        return self.state in (
            DeploymentState.SUCCEEDED,
            DeploymentState.FAILED,
            DeploymentState.ROLLED_BACK,
        )


class DeploymentMetrics(Base):
    """Monitoring metrics for deployed models."""
    __tablename__ = "deployment_metrics"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metrics
    prediction_latency_ms = Column(Float, nullable=True)  # Average latency in ms
    throughput = Column(Float, nullable=True)  # Predictions per second
    error_rate = Column(Float, nullable=True)  # Error rate 0-1
    quality_score = Column(Float, nullable=True)  # Quality metric 0-1
    drift_score = Column(Float, nullable=True)  # Data drift 0-1
    availability = Column(Float, nullable=True)  # Availability 0-1
    last_successful_inference = Column(DateTime, nullable=True)
    monitoring_status = Column(String(50), default="ACTIVE", nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
