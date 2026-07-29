from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import datetime
from app.models.domain import (
    Model,
    ModelVersion,
    Deployment,
    ModelLifecycleStage,
    DeploymentState,
    DeploymentMetrics,
)
from app.schemas import (
    ModelCreateRequest,
    ModelVersionCreateRequest,
    ModelVersionUpdateRequest,
    DeploymentCreateRequest,
)


class ModelService:
    """Service for model management."""

    @staticmethod
    def create_model(db: Session, req: ModelCreateRequest) -> Model:
        """Create a new model."""
        model = Model(
            name=req.name,
            description=req.description,
            owner=req.owner,
            framework=req.framework,
            algorithm=req.algorithm,
        )
        db.add(model)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Model '{req.name}' already exists")
        db.refresh(model)
        return model

    @staticmethod
    def get_model(db: Session, model_id: int) -> Optional[Model]:
        """Get model by ID."""
        return db.query(Model).filter(Model.id == model_id).first()

    @staticmethod
    def get_model_by_name(db: Session, name: str) -> Optional[Model]:
        """Get model by name."""
        return db.query(Model).filter(Model.name == name).first()

    @staticmethod
    def list_models(db: Session, skip: int = 0, limit: int = 100) -> List[Model]:
        """List all models."""
        return db.query(Model).offset(skip).limit(limit).all()


class ModelVersionService:
    """Service for model version management with lifecycle validation."""

    # Valid lifecycle transitions
    VALID_TRANSITIONS = {
        ModelLifecycleStage.DRAFT: [
            ModelLifecycleStage.VALIDATED,
            ModelLifecycleStage.ARCHIVED,
        ],
        ModelLifecycleStage.VALIDATED: [
            ModelLifecycleStage.APPROVED,
            ModelLifecycleStage.ARCHIVED,
            ModelLifecycleStage.DRAFT,
        ],
        ModelLifecycleStage.APPROVED: [
            ModelLifecycleStage.STAGING,
            ModelLifecycleStage.ARCHIVED,
        ],
        ModelLifecycleStage.STAGING: [
            ModelLifecycleStage.PRODUCTION,
            ModelLifecycleStage.ARCHIVED,
        ],
        ModelLifecycleStage.PRODUCTION: [
            ModelLifecycleStage.ARCHIVED,
        ],
        ModelLifecycleStage.ARCHIVED: [],
    }

    @staticmethod
    def create_version(db: Session, model_id: int, req: ModelVersionCreateRequest) -> ModelVersion:
        """Create a new model version in DRAFT stage."""
        model = ModelService.get_model(db, model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        version = ModelVersion(
            model_id=model_id,
            version=req.version,
            artifact_uri=req.artifact_uri,
            training_data_uri=req.training_data_uri,
            metrics=req.metrics,
            tags=req.tags,
            lifecycle_stage=ModelLifecycleStage.DRAFT,
        )
        db.add(version)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Version '{req.version}' already exists for model {model_id}")
        db.refresh(version)
        return version

    @staticmethod
    def get_version(db: Session, version_id: int) -> Optional[ModelVersion]:
        """Get model version by ID."""
        return db.query(ModelVersion).filter(ModelVersion.id == version_id).first()

    @staticmethod
    def list_versions(db: Session, model_id: int) -> List[ModelVersion]:
        """List all versions for a model."""
        return db.query(ModelVersion).filter(ModelVersion.model_id == model_id).all()

    @staticmethod
    def update_lifecycle_stage(
        db: Session,
        version_id: int,
        new_stage: ModelLifecycleStage,
        approved_by: Optional[str] = None,
    ) -> ModelVersion:
        """Update version lifecycle stage with validation."""
        version = ModelVersionService.get_version(db, version_id)
        if not version:
            raise ValueError(f"Version {version_id} not found")

        current_stage = ModelLifecycleStage(version.lifecycle_stage)
        valid_next_stages = ModelVersionService.VALID_TRANSITIONS.get(current_stage, [])

        if new_stage not in valid_next_stages:
            raise ValueError(
                f"Invalid transition from {current_stage} to {new_stage}. "
                f"Valid transitions: {valid_next_stages}"
            )

        version.lifecycle_stage = new_stage
        if approved_by:
            version.approved_by = approved_by
            version.approval_timestamp = datetime.utcnow()
        version.updated_at = datetime.utcnow()

        db.add(version)
        db.commit()
        db.refresh(version)
        return version


class DeploymentService:
    """Service for deployment management with retry, rollback, and idempotency."""

    @staticmethod
    def request_deployment(db: Session, req: DeploymentCreateRequest) -> Deployment:
        """Request a deployment (with idempotency check)."""
        # Check for duplicate request
        existing = db.query(Deployment).filter(
            Deployment.deployment_request_id == req.deployment_request_id
        ).first()
        if existing:
            return existing

        # Get and validate version
        version = ModelVersionService.get_version(db, req.version_id)
        if not version:
            raise ValueError(f"Version {req.version_id} not found")

        # Prevent unapproved versions from going to production
        if req.environment.lower() == "production" and not version.is_approved:
            raise ValueError(
                f"Cannot deploy unapproved version {version.version} to production. "
                f"Current stage: {version.lifecycle_stage}"
            )

        deployment = Deployment(
            model_id=req.model_id,
            version_id=req.version_id,
            environment=req.environment,
            deployed_by=req.deployed_by,
            deployment_request_id=req.deployment_request_id,
            state=DeploymentState.REQUESTED,
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    @staticmethod
    def get_deployment(db: Session, deployment_id: int) -> Optional[Deployment]:
        """Get deployment by ID."""
        return db.query(Deployment).filter(Deployment.id == deployment_id).first()

    @staticmethod
    def list_deployments(
        db: Session,
        model_id: Optional[int] = None,
        environment: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Deployment]:
        """List deployments with optional filters."""
        query = db.query(Deployment)
        if model_id:
            query = query.filter(Deployment.model_id == model_id)
        if environment:
            query = query.filter(Deployment.environment == environment)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def retry_deployment(db: Session, deployment_id: int) -> Deployment:
        """Retry a failed deployment."""
        deployment = DeploymentService.get_deployment(db, deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        if deployment.state != DeploymentState.FAILED:
            raise ValueError(
                f"Can only retry failed deployments. Current state: {deployment.state}"
            )

        # Create a new deployment request with same details
        new_req = DeploymentCreateRequest(
            model_id=deployment.model_id,
            version_id=deployment.version_id,
            environment=deployment.environment,
            deployed_by=deployment.deployed_by,
            deployment_request_id=f"{deployment.deployment_request_id}_retry_{datetime.utcnow().timestamp()}",
        )
        return DeploymentService.request_deployment(db, new_req)

    @staticmethod
    def rollback_deployment(db: Session, deployment_id: int) -> Deployment:
        """Rollback a deployment."""
        deployment = DeploymentService.get_deployment(db, deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        if deployment.state != DeploymentState.SUCCEEDED:
            raise ValueError(
                f"Can only rollback succeeded deployments. Current state: {deployment.state}"
            )

        deployment.state = DeploymentState.ROLLED_BACK
        deployment.completed_at = datetime.utcnow()
        deployment.updated_at = datetime.utcnow()

        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment

    @staticmethod
    def update_deployment_state(
        db: Session,
        deployment_id: int,
        new_state: DeploymentState,
        error_message: Optional[str] = None,
    ) -> Deployment:
        """Update deployment state."""
        deployment = DeploymentService.get_deployment(db, deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        if deployment.is_terminal_state:
            raise ValueError(
                f"Cannot update deployment in terminal state: {deployment.state}"
            )

        deployment.state = new_state
        if error_message:
            deployment.error_message = error_message
        if new_state == DeploymentState.DEPLOYING and not deployment.started_at:
            deployment.started_at = datetime.utcnow()
        if deployment.is_terminal_state:
            deployment.completed_at = datetime.utcnow()
        deployment.updated_at = datetime.utcnow()

        db.add(deployment)
        db.commit()
        db.refresh(deployment)
        return deployment


class MetricsService:
    """Service for deployment metrics."""

    @staticmethod
    def record_metrics(
        db: Session,
        deployment_id: int,
        prediction_latency_ms: Optional[float] = None,
        throughput: Optional[float] = None,
        error_rate: Optional[float] = None,
        quality_score: Optional[float] = None,
        drift_score: Optional[float] = None,
        availability: Optional[float] = None,
        last_successful_inference: Optional[datetime] = None,
    ) -> DeploymentMetrics:
        """Record metrics for a deployment."""
        deployment = DeploymentService.get_deployment(db, deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")

        metrics = DeploymentMetrics(
            deployment_id=deployment_id,
            prediction_latency_ms=prediction_latency_ms,
            throughput=throughput,
            error_rate=error_rate,
            quality_score=quality_score,
            drift_score=drift_score,
            availability=availability,
            last_successful_inference=last_successful_inference,
        )
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        return metrics

    @staticmethod
    def get_latest_metrics(db: Session, deployment_id: int) -> Optional[DeploymentMetrics]:
        """Get latest metrics for deployment."""
        return (
            db.query(DeploymentMetrics)
            .filter(DeploymentMetrics.deployment_id == deployment_id)
            .order_by(DeploymentMetrics.timestamp.desc())
            .first()
        )
