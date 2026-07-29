import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface ErrorState {
  message: string;
  code?: string;
  timestamp?: string;
}

@Injectable({ providedIn: 'root' })
export class ErrorService {
  private errorSubject = new BehaviorSubject<ErrorState | null>(null);
  error$ = this.errorSubject.asObservable();

  setError(error: ErrorState | null): void {
    this.errorSubject.next(error);
  }

  getError(): ErrorState | null {
    return this.errorSubject.value;
  }

  clearError(): void {
    this.errorSubject.next(null);
  }
}
