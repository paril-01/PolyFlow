// storage.ts — PolyFlow TypeScript Contracts matching .poly schemas

export interface SessionContext {
  userId: string;
  email: string;
  sessionToken: string;
  role: 'admin' | 'user';
  expiresAt: number;
}

export interface FileMetadata {
  fileId: string;
  ownerId: string;
  name: string;
  sizeBytes: number;
  mimeType: string;
  storagePath: string;
  checksumSha256: string;
  status: 'PENDING_PROCESSING' | 'READY' | 'ERROR';
  createdAt: number;
}

export interface FolderNode {
  folderId: string;
  parentId: string | null;
  name: string;
  ownerId: string;
  path: string;
  itemCount: number;
}

export interface ShareGrant {
  shareId: string;
  fileId: string;
  granterId: string;
  granteeEmail: string;
  permission: 'READ' | 'WRITE' | 'ADMIN';
  isPublicLink: boolean;
  expiresAt: number;
}
