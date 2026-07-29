import { Component, OnInit, OnDestroy } from '@angular/core';
import { APIService } from '../../services/api.service';
import { LoadingService } from '../../services/loading.service';
import { ErrorService } from '../../services/error.service';
import { ModelMetricsResponse } from '../../models';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-monitoring',
  templateUrl: './monitoring.component.html',
  styleUrls: ['./monitoring.component.scss']
})
export class MonitoringComponent implements OnInit, OnDestroy {
  modelMetrics: Map<number, ModelMetricsResponse> = new Map();
  modelIds: number[] = [1, 2, 3]; // Example model IDs
  loading$ = this.loadingService.loading$;
  error$ = this.errorService.error$;
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: APIService,
    private loadingService: LoadingService,
    private errorService: ErrorService
  ) {}

  ngOnInit(): void {
    this.loadMetrics();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadMetrics(): void {
    this.loadingService.setLoading(true);
    this.modelIds.forEach(modelId => {
      this.apiService.getModelMetrics(modelId)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (metrics) => {
            this.modelMetrics.set(modelId, metrics);
            this.errorService.clearError();
            this.loadingService.setLoading(false);
          },
          error: (error) => {
            // Skip errors for individual models
            console.error(`Failed to load metrics for model ${modelId}:`, error);
          }
        });
    });
  }

  getMetricsArray(): Array<{ id: number; metrics: ModelMetricsResponse }> {
    return Array.from(this.modelMetrics.entries()).map(([id, metrics]) => ({
      id,
      metrics
    }));
  }

  getHealthStatus(availability?: number): string {
    if (!availability) return 'UNKNOWN';
    if (availability >= 0.99) return 'HEALTHY';
    if (availability >= 0.95) return 'WARNING';
    return 'CRITICAL';
  }

  refreshMetrics(): void {
    this.loadMetrics();
  }
}
