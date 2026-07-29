import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal, engine
from app.models.domain import Base, ModelLifecycleStage, DeploymentState


@pytest.fixture(scope="function")
def test_client():
    """Create test client with clean database."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    client = TestClient(app)
    yield client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)


class TestModelAPI:
    """Test model API endpoints."""

    def test_create_model(self, test_client):
        """Test POST /models."""
        response = test_client.post(
            "/api/v1/models",
            json={
                "name": "customer-churn",
                "description": "Predicts customer churn",
                "owner": "data-team",
                "framework": "sklearn",
                "algorithm": "random_forest",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "customer-churn"
        assert data["owner"] == "data-team"
        assert "id" in data
        assert "created_at" in data

    def test_create_duplicate_model_conflict(self, test_client):
        """Test creating duplicate model returns 409."""
        payload = {
            "name": "fraud-detector",
            "owner": "ml-team",
            "framework": "tensorflow",
            "algorithm": "nn",
        }
        
        test_client.post("/api/v1/models", json=payload)
        response = test_client.post("/api/v1/models", json=payload)
        
        assert response.status_code == 409

    def test_list_models(self, test_client):
        """Test GET /models."""
        # Create 3 models
        for i in range(3):
            test_client.post(
                "/api/v1/models",
                json={
                    "name": f"model-{i}",
                    "owner": "team",
                    "framework": "sklearn",
                    "algorithm": "rf",
                }
            )
        
        response = test_client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_model(self, test_client):
        """Test GET /models/{model_id}."""
        create_response = test_client.post(
            "/api/v1/models",
            json={
                "name": "test-model",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = create_response.json()["id"]
        
        response = test_client.get(f"/api/v1/models/{model_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == model_id

    def test_get_nonexistent_model(self, test_client):
        """Test GET nonexistent model returns 404."""
        response = test_client.get("/api/v1/models/999")
        assert response.status_code == 404


class TestModelVersionAPI:
    """Test model version API endpoints."""

    def test_create_version(self, test_client):
        """Test POST /models/{model_id}/versions."""
        # Create model
        model_response = test_client.post(
            "/api/v1/models",
            json={
                "name": "test-model",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = model_response.json()["id"]
        
        # Create version
        response = test_client.post(
            f"/api/v1/models/{model_id}/versions",
            json={
                "version": "1.0.0",
                "artifact_uri": "s3://bucket/v1.0.0/model.pkl",
                "training_data_uri": "s3://bucket/data/train.csv",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["version"] == "1.0.0"
        assert data["lifecycle_stage"] == "DRAFT"
        assert data["is_approved"] == False

    def test_list_versions(self, test_client):
        """Test GET /models/{model_id}/versions."""
        # Create model
        model_response = test_client.post(
            "/api/v1/models",
            json={
                "name": "test-model",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = model_response.json()["id"]
        
        # Create 2 versions
        for i in range(2):
            test_client.post(
                f"/api/v1/models/{model_id}/versions",
                json={
                    "version": f"1.0.{i}",
                    "artifact_uri": f"s3://bucket/v1.0.{i}/model.pkl",
                }
            )
        
        response = test_client.get(f"/api/v1/models/{model_id}/versions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_version_lifecycle(self, test_client):
        """Test PATCH /versions/{version_id}."""
        # Create model and version
        model_response = test_client.post(
            "/api/v1/models",
            json={
                "name": "test-model",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = model_response.json()["id"]
        
        version_response = test_client.post(
            f"/api/v1/models/{model_id}/versions",
            json={
                "version": "1.0.0",
                "artifact_uri": "s3://bucket/v1.0.0/model.pkl",
            }
        )
        version_id = version_response.json()["id"]
        
        # Update to VALIDATED
        response = test_client.patch(
            f"/api/v1/versions/{version_id}",
            json={"lifecycle_stage": "VALIDATED"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_stage"] == "VALIDATED"

    def test_invalid_lifecycle_transition(self, test_client):
        """Test invalid lifecycle transition returns 400."""
        # Create model and version
        model_response = test_client.post(
            "/api/v1/models",
            json={
                "name": "test-model",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = model_response.json()["id"]
        
        version_response = test_client.post(
            f"/api/v1/models/{model_id}/versions",
            json={
                "version": "1.0.0",
                "artifact_uri": "s3://bucket/v1.0.0/model.pkl",
            }
        )
        version_id = version_response.json()["id"]
        
        # Try to go directly to PRODUCTION (invalid)
        response = test_client.patch(
            f"/api/v1/versions/{version_id}",
            json={"lifecycle_stage": "PRODUCTION"}
        )
        
        assert response.status_code == 400


class TestDeploymentAPI:
    """Test deployment API endpoints."""

    def _create_approved_version(self, test_client):
        """Helper to create an approved model version."""
        # Create model
        model_response = test_client.post(
            "/api/v1/models",
            json={
                "name": f"model-{id(test_client)}",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = model_response.json()["id"]
        
        # Create version
        version_response = test_client.post(
            f"/api/v1/models/{model_id}/versions",
            json={
                "version": "1.0.0",
                "artifact_uri": "s3://bucket/v1.0.0/model.pkl",
            }
        )
        version_id = version_response.json()["id"]
        
        # Move through lifecycle
        test_client.patch(
            f"/api/v1/versions/{version_id}",
            json={"lifecycle_stage": "VALIDATED"}
        )
        test_client.patch(
            f"/api/v1/versions/{version_id}",
            json={"lifecycle_stage": "APPROVED", "approved_by": "reviewer@example.com"}
        )
        
        return model_id, version_id

    def test_request_deployment(self, test_client):
        """Test POST /deployments."""
        model_id, version_id = self._create_approved_version(test_client)
        
        response = test_client.post(
            "/api/v1/deployments",
            json={
                "model_id": model_id,
                "version_id": version_id,
                "environment": "staging",
                "deployed_by": "deployer@example.com",
                "deployment_request_id": "deploy-123",
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["state"] == "REQUESTED"
        assert data["environment"] == "staging"

    def test_prevent_unapproved_to_production(self, test_client):
        """Test preventing unapproved version deployment to production."""
        # Create unapproved version
        model_response = test_client.post(
            "/api/v1/models",
            json={
                "name": "test-model-unapproved",
                "owner": "team",
                "framework": "sklearn",
                "algorithm": "rf",
            }
        )
        model_id = model_response.json()["id"]
        
        version_response = test_client.post(
            f"/api/v1/models/{model_id}/versions",
            json={
                "version": "1.0.0",
                "artifact_uri": "s3://bucket/v1.0.0/model.pkl",
            }
        )
        version_id = version_response.json()["id"]
        
        # Try to deploy to production (should fail)
        response = test_client.post(
            "/api/v1/deployments",
            json={
                "model_id": model_id,
                "version_id": version_id,
                "environment": "production",
                "deployed_by": "deployer@example.com",
                "deployment_request_id": "deploy-123",
            }
        )
        
        assert response.status_code == 400

    def test_list_deployments(self, test_client):
        """Test GET /deployments."""
        model_id, version_id = self._create_approved_version(test_client)
        
        # Create 2 deployments
        for i in range(2):
            test_client.post(
                "/api/v1/deployments",
                json={
                    "model_id": model_id,
                    "version_id": version_id,
                    "environment": "staging",
                    "deployed_by": "deployer@example.com",
                    "deployment_request_id": f"deploy-{i}",
                }
            )
        
        response = test_client.get("/api/v1/deployments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_deployment(self, test_client):
        """Test GET /deployments/{deployment_id}."""
        model_id, version_id = self._create_approved_version(test_client)
        
        deploy_response = test_client.post(
            "/api/v1/deployments",
            json={
                "model_id": model_id,
                "version_id": version_id,
                "environment": "staging",
                "deployed_by": "deployer@example.com",
                "deployment_request_id": "deploy-123",
            }
        )
        deployment_id = deploy_response.json()["id"]
        
        response = test_client.get(f"/api/v1/deployments/{deployment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == deployment_id

    def test_rollback_deployment(self, test_client):
        """Test POST /deployments/{deployment_id}/rollback."""
        model_id, version_id = self._create_approved_version(test_client)
        
        deploy_response = test_client.post(
            "/api/v1/deployments",
            json={
                "model_id": model_id,
                "version_id": version_id,
                "environment": "production",
                "deployed_by": "deployer@example.com",
                "deployment_request_id": "deploy-123",
            }
        )
        deployment_id = deploy_response.json()["id"]
        
        # Manually set to SUCCEEDED (in real scenario, would happen through deployment process)
        # For this test, we simulate by checking the rollback endpoint behavior
        response = test_client.post(
            f"/api/v1/deployments/{deployment_id}/rollback"
        )
        
        # Should fail because deployment is still in REQUESTED state
        assert response.status_code == 400


class TestHealthAPI:
    """Test health check endpoint."""

    def test_health_check(self, test_client):
        """Test GET /health."""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
