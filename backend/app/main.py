from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime
import logging

from app.database import init_db
from app.api.routes import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MLOps Platform API",
    description="Model registry, deployment, and monitoring platform",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect to API documentation."""
    return JSONResponse({
        "message": "MLOps Platform API",
        "version": "1.0.0",
        "docs": "http://localhost:8000/docs",
        "api": "http://localhost:8000/api/v1",
        "tester": "http://localhost:8000/tester"
    })


@app.get("/tester", include_in_schema=False, response_class=HTMLResponse)
async def api_tester():
    """Simple API tester interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MLOps Platform API Tester</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #333; margin-bottom: 30px; text-align: center; }
            .section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .section h2 { color: #0066cc; margin-bottom: 15px; font-size: 18px; }
            .endpoint { margin: 15px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #0066cc; }
            .endpoint h3 { font-size: 14px; color: #333; margin-bottom: 10px; }
            .endpoint p { font-size: 12px; color: #666; margin-bottom: 10px; }
            .btn { background: #0066cc; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 12px; }
            .btn:hover { background: #0052a3; }
            .result { background: #f0f0f0; padding: 10px; border-radius: 4px; margin-top: 10px; font-family: monospace; font-size: 11px; max-height: 300px; overflow-y: auto; white-space: pre-wrap; }
            .success { border-left-color: #28a745; }
            .error { border-left-color: #dc3545; color: #dc3545; }
            input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 12px; }
            label { display: block; margin-top: 10px; font-weight: bold; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MLOps Platform API Tester</h1>
            
            <div class="section">
                <h2>1️⃣ Health Check</h2>
                <div class="endpoint success">
                    <h3>GET /health</h3>
                    <button class="btn" onclick="testHealth()">Test</button>
                    <div id="health-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>2️⃣ Create Model</h2>
                <div class="endpoint success">
                    <h3>POST /api/v1/models</h3>
                    <label>Model Name:</label>
                    <input type="text" id="model-name" placeholder="fraud-detection" value="fraud-detection">
                    <label>Owner:</label>
                    <input type="text" id="model-owner" placeholder="data-team" value="data-team">
                    <label>Framework:</label>
                    <input type="text" id="model-framework" placeholder="pytorch" value="pytorch">
                    <button class="btn" onclick="createModel()">Create Model</button>
                    <div id="model-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>3️⃣ List Models</h2>
                <div class="endpoint success">
                    <h3>GET /api/v1/models</h3>
                    <button class="btn" onclick="listModels()">List Models</button>
                    <div id="list-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>4️⃣ Create Model Version</h2>
                <div class="endpoint success">
                    <h3>POST /api/v1/models/{id}/versions</h3>
                    <label>Model ID:</label>
                    <input type="number" id="version-model-id" placeholder="1" value="1">
                    <label>Version:</label>
                    <input type="text" id="version-number" placeholder="1.0.0" value="1.0.0">
                    <label>Artifact URI:</label>
                    <input type="text" id="artifact-uri" placeholder="s3://bucket/model.pkl" value="s3://bucket/model.pkl">
                    <button class="btn" onclick="createVersion()">Create Version</button>
                    <div id="version-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>5️⃣ Update Version Lifecycle</h2>
                <div class="endpoint success">
                    <h3>PATCH /api/v1/versions/{id}</h3>
                    <label>Version ID:</label>
                    <input type="number" id="approve-version-id" placeholder="1" value="1">
                    <label>Lifecycle Stage:</label>
                    <select id="lifecycle-stage" style="width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; font-size: 12px;">
                        <option value="VALIDATED">VALIDATED (Step 1)</option>
                        <option value="APPROVED">APPROVED (Step 2)</option>
                        <option value="STAGING">STAGING (Step 3)</option>
                        <option value="PRODUCTION">PRODUCTION (Step 4)</option>
                        <option value="ARCHIVED">ARCHIVED</option>
                    </select>
                    <button class="btn" onclick="updateLifecycle()">Update</button>
                    <div id="approve-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>6️⃣ Request Deployment</h2>
                <div class="endpoint success">
                    <h3>POST /api/v1/deployments</h3>
                    <label>Model ID:</label>
                    <input type="number" id="deploy-model-id" placeholder="1" value="1">
                    <label>Version ID:</label>
                    <input type="number" id="deploy-version-id" placeholder="2" value="2">
                    <label>Environment:</label>
                    <input type="text" id="deploy-env" placeholder="production" value="production">
                    <label>Deployed By:</label>
                    <input type="text" id="deploy-by" placeholder="deployer@example.com" value="deployer@example.com">
                    <button class="btn" onclick="requestDeployment()">Deploy</button>
                    <div id="deploy-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>7️⃣ Retry Failed Deployment</h2>
                <div class="endpoint success">
                    <h3>POST /api/v1/deployments/{id}/retry</h3>
                    <label>Deployment ID:</label>
                    <input type="number" id="retry-deploy-id" placeholder="1" value="1">
                    <button class="btn" onclick="retryDeployment()">Retry</button>
                    <div id="retry-result" class="result"></div>
                </div>
            </div>

            <div class="section">
                <h2>9️⃣ Get Model Metrics</h2>
                <div class="endpoint success">
                    <h3>GET /api/v1/models/{id}/metrics</h3>
                    <label>Model ID:</label>
                    <input type="number" id="metrics-model-id" placeholder="1" value="1">
                    <button class="btn" onclick="getMetrics()">Get Metrics</button>
                    <div id="metrics-result" class="result"></div>
                </div>
            </div>
        </div>

        <script>
            const API = "http://localhost:8000/api/v1";
            
            async function testHealth() {
                try {
                    const res = await fetch(API + "/health");
                    const data = await res.json();
                    document.getElementById("health-result").textContent = JSON.stringify(data, null, 2);
                } catch(e) {
                    document.getElementById("health-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function createModel() {
                const data = {
                    name: document.getElementById("model-name").value,
                    owner: document.getElementById("model-owner").value,
                    framework: document.getElementById("model-framework").value,
                    description: "Test model",
                    algorithm: "neural_network"
                };
                try {
                    const res = await fetch(API + "/models", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data)
                    });
                    const result = await res.json();
                    document.getElementById("model-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("model-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function listModels() {
                try {
                    const res = await fetch(API + "/models");
                    const data = await res.json();
                    document.getElementById("list-result").textContent = JSON.stringify(data, null, 2);
                } catch(e) {
                    document.getElementById("list-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function createVersion() {
                const data = {
                    version: document.getElementById("version-number").value,
                    artifact_uri: document.getElementById("artifact-uri").value,
                    training_data_uri: "s3://bucket/train.csv"
                };
                const modelId = document.getElementById("version-model-id").value;
                try {
                    const res = await fetch(API + "/models/" + modelId + "/versions", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data)
                    });
                    const result = await res.json();
                    document.getElementById("version-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("version-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function updateLifecycle() {
                const data = { 
                    lifecycle_stage: document.getElementById("lifecycle-stage").value,
                    approved_by: "reviewer@example.com" 
                };
                const versionId = document.getElementById("approve-version-id").value;
                try {
                    const res = await fetch(API + "/versions/" + versionId, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data)
                    });
                    const result = await res.json();
                    document.getElementById("approve-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("approve-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function requestDeployment() {
                const data = {
                    model_id: parseInt(document.getElementById("deploy-model-id").value),
                    version_id: parseInt(document.getElementById("deploy-version-id").value),
                    environment: document.getElementById("deploy-env").value,
                    deployed_by: document.getElementById("deploy-by").value,
                    deployment_request_id: "deploy-" + Date.now()
                };
                try {
                    const res = await fetch(API + "/deployments", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(data)
                    });
                    const result = await res.json();
                    document.getElementById("deploy-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("deploy-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function retryDeployment() {
                const deploymentId = document.getElementById("retry-deploy-id").value;
                try {
                    const res = await fetch(API + "/deployments/" + deploymentId + "/retry", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" }
                    });
                    const result = await res.json();
                    document.getElementById("retry-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("retry-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function rollbackDeployment() {
                const deploymentId = document.getElementById("rollback-deploy-id").value;
                try {
                    const res = await fetch(API + "/deployments/" + deploymentId + "/rollback", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" }
                    });
                    const result = await res.json();
                    document.getElementById("rollback-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("rollback-result").textContent = "❌ Error: " + e.message;
                }
            }

            async function getMetrics() {
                const modelId = document.getElementById("metrics-model-id").value;
                try {
                    const res = await fetch(API + "/models/" + modelId + "/metrics");
                    const result = await res.json();
                    document.getElementById("metrics-result").textContent = JSON.stringify(result, null, 2);
                } catch(e) {
                    document.getElementById("metrics-result").textContent = "❌ Error: " + e.message;
                }
            }
        </script>
    </body>
    </html>
    """


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
