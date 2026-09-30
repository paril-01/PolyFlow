package polyflow.storage;

public class StorageValidator {
    public static boolean validateUpload(String fileName, long sizeBytes, String mimeType) {
        if (fileName == null || fileName.trim().isEmpty()) return false;
        if (sizeBytes <= 0 || sizeBytes > 500L * 1024 * 1024) return false;
        if (mimeType == null || !mimeType.contains("/")) return false;
        return true;
    }
}
