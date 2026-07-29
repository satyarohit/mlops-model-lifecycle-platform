import pytest
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, init_db
from app.models.domain import Base, ModelLifecycleStage, DeploymentState
from app.services import ModelService, ModelVersionService, DeploymentService, MetricsService
from app.schemas import (
    ModelCreateRequest,
    ModelVersionCreateRequest,
    ModelVersionUpdateRequest,
    DeploymentCreateRequest,
)


@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestModelService:
    """Test model service."""

    def test_create_model(self, db_session: Session):
        """Test creating a model."""
        req = ModelCreateRequest(
            name="customer-churn",
            description="Predicts customer churn",
            owner="data-science-team",
            framework="sklearn",
            algorithm="random_forest",
        )
        model = ModelService.create_model(db_session, req)
        
        assert model.id is not None
        assert model.name == "customer-churn"
        assert model.owner == "data-science-team"

    def test_create_duplicate_model_raises_error(self, db_session: Session):
        """Test creating duplicate model raises error."""
        req = ModelCreateRequest(
            name="customer-churn",
            description="Predicts customer churn",
            owner="data-science-team",
            framework="sklearn",
            algorithm="random_forest",
        )
        ModelService.create_model(db_session, req)
        
        with pytest.raises(ValueError, match="already exists"):
            ModelService.create_model(db_session, req)

    def test_get_model(self, db_session: Session):
        """Test retrieving a model."""
        req = ModelCreateRequest(
            name="fraud-detection",
            description="Detects fraudulent transactions",
            owner="ml-team",
            framework="tensorflow",
            algorithm="neural_network",
        )
        model = ModelService.create_model(db_session, req)
        retrieved = ModelService.get_model(db_session, model.id)
        
        assert retrieved.id == model.id
        assert retrieved.name == "fraud-detection"

    def test_list_models(self, db_session: Session):
        """Test listing models."""
        for i in range(3):
            req = ModelCreateRequest(
                name=f"model-{i}",
                owner="team",
                framework="sklearn",
                algorithm="rf",
            )
            ModelService.create_model(db_session, req)
        
        models = ModelService.list_models(db_session)
        assert len(models) == 3


class TestModelVersionService:
    """Test model version service with lifecycle validation."""

    def test_create_version_in_draft_stage(self, db_session: Session):
        """Test creating a version starts in DRAFT stage."""
        model_req = ModelCreateRequest(
            name="test-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        
        assert version.lifecycle_stage == ModelLifecycleStage.DRAFT
        assert not version.is_approved

    def test_valid_transition_draft_to_validated(self, db_session: Session):
        """Test valid transition DRAFT -> VALIDATED."""
        model_req = ModelCreateRequest(
            name="test-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        
        update_req = ModelVersionUpdateRequest(
            lifecycle_stage=ModelLifecycleStage.VALIDATED
        )
        updated = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, update_req.lifecycle_stage
        )
        
        assert updated.lifecycle_stage == ModelLifecycleStage.VALIDATED

    def test_invalid_transition_raises_error(self, db_session: Session):
        """Test invalid transition raises error."""
        model_req = ModelCreateRequest(
            name="test-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        
        # Cannot go from DRAFT directly to PRODUCTION
        with pytest.raises(ValueError, match="Invalid transition"):
            ModelVersionService.update_lifecycle_stage(
                db_session, version.id, ModelLifecycleStage.PRODUCTION
            )

    def test_path_draft_to_production(self, db_session: Session):
        """Test complete path from DRAFT to PRODUCTION."""
        model_req = ModelCreateRequest(
            name="prod-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        
        # DRAFT -> VALIDATED
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.VALIDATED
        )
        assert version.lifecycle_stage == ModelLifecycleStage.VALIDATED
        
        # VALIDATED -> APPROVED
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.APPROVED, approved_by="reviewer@example.com"
        )
        assert version.lifecycle_stage == ModelLifecycleStage.APPROVED
        assert version.approved_by == "reviewer@example.com"
        assert version.approval_timestamp is not None
        
        # APPROVED -> STAGING
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.STAGING
        )
        assert version.lifecycle_stage == ModelLifecycleStage.STAGING
        
        # STAGING -> PRODUCTION
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.PRODUCTION
        )
        assert version.lifecycle_stage == ModelLifecycleStage.PRODUCTION
        assert version.is_approved


class TestDeploymentService:
    """Test deployment service with idempotency and validation."""

    def _setup_approved_version(self, db_session: Session):
        """Helper to create an approved model version."""
        model_req = ModelCreateRequest(
            name="test-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        
        # Move to APPROVED
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.VALIDATED
        )
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.APPROVED
        )
        
        return model, version

    def test_deployment_request_creates_deployment(self, db_session: Session):
        """Test deployment request creates a deployment."""
        model, version = self._setup_approved_version(db_session)
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="staging",
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        deployment = DeploymentService.request_deployment(db_session, deploy_req)
        
        assert deployment.state == DeploymentState.REQUESTED
        assert deployment.environment == "staging"
        assert deployment.deployment_request_id == "deploy-123"

    def test_duplicate_deployment_request_idempotency(self, db_session: Session):
        """Test duplicate deployment request returns existing deployment."""
        model, version = self._setup_approved_version(db_session)
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="staging",
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        deployment1 = DeploymentService.request_deployment(db_session, deploy_req)
        deployment2 = DeploymentService.request_deployment(db_session, deploy_req)
        
        assert deployment1.id == deployment2.id

    def test_prevent_unapproved_version_to_production(self, db_session: Session):
        """Test unapproved version cannot deploy to production."""
        model_req = ModelCreateRequest(
            name="test-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="production",  # Try to deploy unapproved to production
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        
        with pytest.raises(ValueError, match="Cannot deploy unapproved version"):
            DeploymentService.request_deployment(db_session, deploy_req)

    def test_retry_failed_deployment(self, db_session: Session):
        """Test retrying a failed deployment."""
        model, version = self._setup_approved_version(db_session)
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="staging",
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        deployment = DeploymentService.request_deployment(db_session, deploy_req)
        
        # Update to FAILED
        deployment = DeploymentService.update_deployment_state(
            db_session, deployment.id, DeploymentState.FAILED, "Connection timeout"
        )
        assert deployment.state == DeploymentState.FAILED
        
        # Retry
        retried = DeploymentService.retry_deployment(db_session, deployment.id)
        assert retried.state == DeploymentState.REQUESTED
        assert retried.id != deployment.id  # Should create new deployment

    def test_rollback_succeeded_deployment(self, db_session: Session):
        """Test rolling back a succeeded deployment."""
        model, version = self._setup_approved_version(db_session)
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="production",
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        deployment = DeploymentService.request_deployment(db_session, deploy_req)
        
        # Update to SUCCEEDED
        deployment = DeploymentService.update_deployment_state(
            db_session, deployment.id, DeploymentState.SUCCEEDED
        )
        assert deployment.state == DeploymentState.SUCCEEDED
        
        # Rollback
        rolled_back = DeploymentService.rollback_deployment(db_session, deployment.id)
        assert rolled_back.state == DeploymentState.ROLLED_BACK
        assert rolled_back.completed_at is not None

    def test_cannot_retry_succeeded_deployment(self, db_session: Session):
        """Test cannot retry a succeeded deployment."""
        model, version = self._setup_approved_version(db_session)
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="staging",
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        deployment = DeploymentService.request_deployment(db_session, deploy_req)
        
        # Update to SUCCEEDED
        deployment = DeploymentService.update_deployment_state(
            db_session, deployment.id, DeploymentState.SUCCEEDED
        )
        
        # Try to retry (should fail)
        with pytest.raises(ValueError, match="Can only retry failed"):
            DeploymentService.retry_deployment(db_session, deployment.id)


class TestMetricsService:
    """Test metrics service."""

    def test_record_metrics(self, db_session: Session):
        """Test recording deployment metrics."""
        model_req = ModelCreateRequest(
            name="test-model",
            owner="team",
            framework="sklearn",
            algorithm="rf",
        )
        model = ModelService.create_model(db_session, model_req)
        
        version_req = ModelVersionCreateRequest(
            version="1.0.0",
            artifact_uri="s3://bucket/v1.0.0/model.pkl",
        )
        version = ModelVersionService.create_version(db_session, model.id, version_req)
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.VALIDATED
        )
        version = ModelVersionService.update_lifecycle_stage(
            db_session, version.id, ModelLifecycleStage.APPROVED
        )
        
        deploy_req = DeploymentCreateRequest(
            model_id=model.id,
            version_id=version.id,
            environment="staging",
            deployed_by="deployer@example.com",
            deployment_request_id="deploy-123",
        )
        deployment = DeploymentService.request_deployment(db_session, deploy_req)
        
        metrics = MetricsService.record_metrics(
            db_session,
            deployment.id,
            prediction_latency_ms=45.5,
            throughput=1200.0,
            error_rate=0.01,
            quality_score=0.95,
            drift_score=0.05,
            availability=0.999,
        )
        
        assert metrics.prediction_latency_ms == 45.5
        assert metrics.throughput == 1200.0
        assert metrics.error_rate == 0.01
        assert metrics.quality_score == 0.95
