export type ModelLifecycleStage = 'DRAFT' | 'VALIDATED' | 'APPROVED' | 'STAGING' | 'PRODUCTION' | 'ARCHIVED';
export type DeploymentState = 'REQUESTED' | 'VALIDATING' | 'DEPLOYING' | 'SUCCEEDED' | 'FAILED' | 'ROLLED_BACK';

export interface ModelVersion {
  id: number;
  model_id: number;
  version: string;
  lifecycle_stage: ModelLifecycleStage;
  artifact_uri: string;
  training_data_uri?: string;
  metrics?: Record<string, any>;
  tags?: string;
  approved_by?: string;
  approval_timestamp?: string;
  created_at: string;
  updated_at: string;
  is_approved: boolean;
}

export interface Model {
  id: number;
  name: string;
  description?: string;
  owner: string;
  framework: string;
  algorithm: string;
  created_at: string;
  updated_at: string;
  versions: ModelVersion[];
}

export interface DeploymentMetrics {
  id: number;
  deployment_id: number;
  timestamp: string;
  prediction_latency_ms?: number;
  throughput?: number;
  error_rate?: number;
  quality_score?: number;
  drift_score?: number;
  availability?: number;
  last_successful_inference?: string;
  monitoring_status: string;
  created_at: string;
}

export interface Deployment {
  id: number;
  model_id: number;
  version_id: number;
  environment: string;
  state: DeploymentState;
  deployment_request_id: string;
  error_message?: string;
  deployed_by: string;
  requested_at: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  is_terminal_state: boolean;
}

export interface ModelMetricsResponse {
  model_id: number;
  latest_metrics?: DeploymentMetrics;
  environment_deployments: Record<string, Deployment>;
}
