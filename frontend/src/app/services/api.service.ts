import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { 
  Model, 
  ModelVersion, 
  Deployment, 
  DeploymentMetrics,
  ModelMetricsResponse 
} from '../models';

@Injectable({ providedIn: 'root' })
export class APIService {
  private apiUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  // Models
  createModel(data: any): Observable<Model> {
    return this.http.post<Model>(`${this.apiUrl}/models`, data).pipe(
      catchError(this.handleError)
    );
  }

  getModels(skip: number = 0, limit: number = 100): Observable<Model[]> {
    return this.http.get<Model[]>(`${this.apiUrl}/models`, {
      params: { skip: skip.toString(), limit: limit.toString() }
    }).pipe(
      catchError(this.handleError)
    );
  }

  getModel(modelId: number): Observable<Model> {
    return this.http.get<Model>(`${this.apiUrl}/models/${modelId}`).pipe(
      catchError(this.handleError)
    );
  }

  // Model Versions
  createVersion(modelId: number, data: any): Observable<ModelVersion> {
    return this.http.post<ModelVersion>(`${this.apiUrl}/models/${modelId}/versions`, data).pipe(
      catchError(this.handleError)
    );
  }

  getVersions(modelId: number): Observable<ModelVersion[]> {
    return this.http.get<ModelVersion[]>(`${this.apiUrl}/models/${modelId}/versions`).pipe(
      catchError(this.handleError)
    );
  }

  updateVersionLifecycle(versionId: number, data: any): Observable<ModelVersion> {
    return this.http.patch<ModelVersion>(`${this.apiUrl}/versions/${versionId}`, data).pipe(
      catchError(this.handleError)
    );
  }

  // Deployments
  requestDeployment(data: any): Observable<Deployment> {
    return this.http.post<Deployment>(`${this.apiUrl}/deployments`, data).pipe(
      catchError(this.handleError)
    );
  }

  getDeployments(modelId?: number, environment?: string): Observable<Deployment[]> {
    let params: any = {};
    if (modelId) params.model_id = modelId;
    if (environment) params.environment = environment;
    
    return this.http.get<Deployment[]>(`${this.apiUrl}/deployments`, { params }).pipe(
      catchError(this.handleError)
    );
  }

  getDeployment(deploymentId: number): Observable<Deployment> {
    return this.http.get<Deployment>(`${this.apiUrl}/deployments/${deploymentId}`).pipe(
      catchError(this.handleError)
    );
  }

  retryDeployment(deploymentId: number): Observable<Deployment> {
    return this.http.post<Deployment>(
      `${this.apiUrl}/deployments/${deploymentId}/retry`, 
      {}
    ).pipe(
      catchError(this.handleError)
    );
  }

  rollbackDeployment(deploymentId: number): Observable<Deployment> {
    return this.http.post<Deployment>(
      `${this.apiUrl}/deployments/${deploymentId}/rollback`, 
      {}
    ).pipe(
      catchError(this.handleError)
    );
  }

  // Metrics
  getModelMetrics(modelId: number): Observable<ModelMetricsResponse> {
    return this.http.get<ModelMetricsResponse>(`${this.apiUrl}/models/${modelId}/metrics`).pipe(
      catchError(this.handleError)
    );
  }

  // Health
  health(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`).pipe(
      catchError(this.handleError)
    );
  }

  private handleError(error: any): Observable<never> {
    console.error('API error:', error);
    const errorMessage = error.error?.detail || error.message || 'An error occurred';
    return throwError(() => new Error(errorMessage));
  }
}
