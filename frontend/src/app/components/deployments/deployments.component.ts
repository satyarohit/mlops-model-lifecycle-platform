import { Component, OnInit, OnDestroy } from '@angular/core';
import { APIService } from '../../services/api.service';
import { LoadingService } from '../../services/loading.service';
import { ErrorService } from '../../services/error.service';
import { Deployment } from '../../models';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-deployments',
  templateUrl: './deployments.component.html',
  styleUrls: ['./deployments.component.scss']
})
export class DeploymentsComponent implements OnInit, OnDestroy {
  deployments: Deployment[] = [];
  loading$ = this.loadingService.loading$;
  error$ = this.errorService.error$;
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: APIService,
    private loadingService: LoadingService,
    private errorService: ErrorService
  ) {}

  ngOnInit(): void {
    this.loadDeployments();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadDeployments(): void {
    this.loadingService.setLoading(true);
    this.apiService.getDeployments()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (deployments) => {
          this.deployments = deployments;
          this.errorService.clearError();
          this.loadingService.setLoading(false);
        },
        error: (error) => {
          this.errorService.setError({
            message: error.message || 'Failed to load deployments',
            code: 'LOAD_DEPLOYMENTS_ERROR'
          });
          this.loadingService.setLoading(false);
        }
      });
  }

  getStateColor(state: string): string {
    const colors: Record<string, string> = {
      'REQUESTED': '#ffc107',
      'VALIDATING': '#2196f3',
      'DEPLOYING': '#2196f3',
      'SUCCEEDED': '#4caf50',
      'FAILED': '#f44336',
      'ROLLED_BACK': '#ff9800'
    };
    return colors[state] || '#999';
  }

  retryDeployment(deployment: Deployment): void {
    if (deployment.state === 'FAILED') {
      this.apiService.retryDeployment(deployment.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => this.loadDeployments(),
          error: (error) => this.errorService.setError({
            message: error.message,
            code: 'RETRY_FAILED'
          })
        });
    }
  }

  rollbackDeployment(deployment: Deployment): void {
    if (deployment.state === 'SUCCEEDED') {
      this.apiService.rollbackDeployment(deployment.id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: () => this.loadDeployments(),
          error: (error) => this.errorService.setError({
            message: error.message,
            code: 'ROLLBACK_FAILED'
          })
        });
    }
  }

  refreshDeployments(): void {
    this.loadDeployments();
  }
}
