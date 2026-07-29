import { Component, OnInit, OnDestroy } from '@angular/core';
import { APIService } from '../../services/api.service';
import { LoadingService } from '../../services/loading.service';
import { ErrorService } from '../../services/error.service';
import { Model } from '../../models';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-model-inventory',
  templateUrl: './model-inventory.component.html',
  styleUrls: ['./model-inventory.component.scss']
})
export class ModelInventoryComponent implements OnInit, OnDestroy {
  models: Model[] = [];
  loading$ = this.loadingService.loading$;
  error$ = this.errorService.error$;
  private destroy$ = new Subject<void>();

  displayedColumns: string[] = ['id', 'name', 'owner', 'framework', 'versions', 'created_at', 'actions'];

  constructor(
    private apiService: APIService,
    private loadingService: LoadingService,
    private errorService: ErrorService
  ) {}

  ngOnInit(): void {
    this.loadModels();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadModels(): void {
    this.loadingService.setLoading(true);
    this.apiService.getModels()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (models) => {
          this.models = models;
          this.errorService.clearError();
          this.loadingService.setLoading(false);
        },
        error: (error) => {
          this.errorService.setError({
            message: error.message || 'Failed to load models',
            code: 'LOAD_MODELS_ERROR'
          });
          this.loadingService.setLoading(false);
        }
      });
  }

  getVersionCount(model: Model): number {
    return model.versions ? model.versions.length : 0;
  }

  getApprovedVersionCount(model: Model): number {
    return model.versions ? model.versions.filter(v => v.is_approved).length : 0;
  }

  viewModel(modelId: number): void {
    // Navigate to model detail
    console.log('Navigate to model:', modelId);
  }

  refreshModels(): void {
    this.loadModels();
  }
}
