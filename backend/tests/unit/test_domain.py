import pytest
from datetime import datetime
from app.models.domain import (
    ModelLifecycleStage,
    DeploymentState,
    Model,
    ModelVersion,
    Deployment,
)


class TestModelLifecycleValidation:
    """Test model version lifecycle transitions."""

    def test_draft_to_validated(self):
        """Test DRAFT -> VALIDATED transition."""
        version = ModelVersion(
            model_id=1,
            version="1.0.0",
            artifact_uri="s3://bucket/model.pkl",
            lifecycle_stage=ModelLifecycleStage.DRAFT,
        )
        assert version.lifecycle_stage == ModelLifecycleStage.DRAFT
        assert not version.is_approved

    def test_validated_to_approved(self):
        """Test VALIDATED -> APPROVED transition."""
        version = ModelVersion(
            model_id=1,
            version="1.0.0",
            artifact_uri="s3://bucket/model.pkl",
            lifecycle_stage=ModelLifecycleStage.VALIDATED,
        )
        version.lifecycle_stage = ModelLifecycleStage.APPROVED
        assert version.is_approved

    def test_approved_version_is_deployable(self):
        """Test approved version can be deployed."""
        version = ModelVersion(
            model_id=1,
            version="1.0.0",
            artifact_uri="s3://bucket/model.pkl",
            lifecycle_stage=ModelLifecycleStage.APPROVED,
        )
        assert version.is_approved

    def test_production_version_is_deployable(self):
        """Test production version can be deployed."""
        version = ModelVersion(
            model_id=1,
            version="1.0.0",
            artifact_uri="s3://bucket/model.pkl",
            lifecycle_stage=ModelLifecycleStage.PRODUCTION,
        )
        assert version.is_approved


class TestDeploymentStates:
    """Test deployment state transitions."""

    def test_deployment_requested_state(self):
        """Test deployment starts in REQUESTED state."""
        deployment = Deployment(
            model_id=1,
            version_id=1,
            environment="staging",
            deployed_by="user@example.com",
            deployment_request_id="req-123",
            state=DeploymentState.REQUESTED,
        )
        assert deployment.state == DeploymentState.REQUESTED
        assert not deployment.is_terminal_state

    def test_deployment_succeeded_terminal_state(self):
        """Test SUCCEEDED is a terminal state."""
        deployment = Deployment(
            model_id=1,
            version_id=1,
            environment="production",
            deployed_by="user@example.com",
            deployment_request_id="req-123",
            state=DeploymentState.SUCCEEDED,
        )
        assert deployment.is_terminal_state

    def test_deployment_failed_terminal_state(self):
        """Test FAILED is a terminal state."""
        deployment = Deployment(
            model_id=1,
            version_id=1,
            environment="staging",
            deployed_by="user@example.com",
            deployment_request_id="req-123",
            state=DeploymentState.FAILED,
        )
        assert deployment.is_terminal_state

    def test_deployment_rolled_back_terminal_state(self):
        """Test ROLLED_BACK is a terminal state."""
        deployment = Deployment(
            model_id=1,
            version_id=1,
            environment="production",
            deployed_by="user@example.com",
            deployment_request_id="req-123",
            state=DeploymentState.ROLLED_BACK,
        )
        assert deployment.is_terminal_state
