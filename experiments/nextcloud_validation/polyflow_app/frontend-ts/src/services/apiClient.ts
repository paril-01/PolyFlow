// apiClient.ts — Frontend API client connecting to PolyFlow storage API

import { SessionContext, FileMetadata, FolderNode, ShareGrant } from '../types/storage';

export class StorageApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8080/api/v1') {
    this.baseUrl = baseUrl;
  }

  public setToken(token: string): void {
    this.token = token;
  }

  public formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  public validateUploadParams(fileName: string, sizeBytes: number): { valid: boolean; error?: string } {
    if (!fileName || fileName.trim().length === 0) {
      return { valid: false, error: 'File name cannot be empty' };
    }
    if (sizeBytes <= 0) {
      return { valid: false, error: 'File size must be greater than zero' };
    }
    if (sizeBytes > 500 * 1024 * 1024) {
      return { valid: false, error: 'File exceeds maximum size limit of 500MB' };
    }
    return { valid: true };
  }
}
