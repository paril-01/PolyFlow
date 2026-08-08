import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-config-history',
  template: `
    <div class="p-4 bg-white rounded shadow-sm border">
      <h3 class="text-lg font-semibold">Config History</h3>
      <button (click)="execute()" [disabled]="loading"
              class="mt-3 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
        {{ loading ? 'Processing...' : 'Execute' }}
      </button>
      <div *ngIf="error" class="mt-2 text-red-500">{{ error }}</div>
      <pre *ngIf="result" class="mt-2 p-2 bg-gray-50 rounded text-xs">{{ result | json }}</pre>
    </div>
  `
})
export class ConfigHistoryComponent {
  loading = false;
  result: any = null;
  error: string | null = null;

  constructor(private http: HttpClient) {}

  execute() {
    this.loading = true;
    this.error = null;
    this.http.post('/api/v1/admin/config-history', {}).subscribe({
      next: (data) => { this.result = data; this.loading = false; },
      error: (err) => { this.error = err.message; this.loading = false; },
    });
  }
}
