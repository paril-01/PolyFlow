package polyflow.storage;

public class StorageService {
    public static class FileRecord {
        public final String fileId;
        public final String name;
        public final long sizeBytes;
        public final String mimeType;
        public final String status;

        public FileRecord(String fileId, String name, long sizeBytes, String mimeType, String status) {
            this.fileId = fileId;
            this.name = name;
            this.sizeBytes = sizeBytes;
            this.mimeType = mimeType;
            this.status = status;
        }
    }

    public static FileRecord processUpload(String userRole, String grantPermission, String fileName, long sizeBytes, String mimeType) {
        if (!PermissionChecker.hasAccess(userRole, grantPermission, "WRITE")) {
            throw new SecurityException("User not authorized to upload file");
        }
        if (!StorageValidator.validateUpload(fileName, sizeBytes, mimeType)) {
            throw new IllegalArgumentException("Invalid file payload specifications");
        }
        String fileId = "file_" + Math.abs(fileName.hashCode()) + "_" + (System.currentTimeMillis() % 100000);
        return new FileRecord(fileId, fileName, sizeBytes, mimeType, "PENDING_PROCESSING");
    }
}
