package polyflow.storage;

public class TestStorageSuite {
    public static void main(String[] args) {
        System.out.println("Running PolyFlow Storage Java Test Suite (JVM 21)...");
        int passed = 0;
        int failed = 0;

        // Test 1: Validator accepts valid file
        if (StorageValidator.validateUpload("document.pdf", 1024 * 50, "application/pdf")) {
            System.out.println("  [PASS] Test 1: Validator accepted valid document.pdf");
            passed++;
        } else {
            System.out.println("  [FAIL] Test 1: Validator rejected valid file");
            failed++;
        }

        // Test 2: Validator rejects oversized file
        if (!StorageValidator.validateUpload("huge.iso", 600L * 1024 * 1024, "application/octet-stream")) {
            System.out.println("  [PASS] Test 2: Validator rejected oversized file (>500MB)");
            passed++;
        } else {
            System.out.println("  [FAIL] Test 2: Validator accepted oversized file");
            failed++;
        }

        // Test 3: Permission checker enforces WRITE
        if (PermissionChecker.hasAccess("user", "WRITE", "WRITE") &&
            !PermissionChecker.hasAccess("user", "READ", "WRITE") &&
            PermissionChecker.hasAccess("admin", "NONE", "WRITE")) {
            System.out.println("  [PASS] Test 3: Permission checker correctly verified capabilities");
            passed++;
        } else {
            System.out.println("  [FAIL] Test 3: Permission checker failed rule logic");
            failed++;
        }

        // Test 4: Storage service creates record
        try {
            StorageService.FileRecord rec = StorageService.processUpload("user", "WRITE", "report.docx", 20480, "application/vnd.word");
            if (rec != null && "PENDING_PROCESSING".equals(rec.status) && rec.fileId.startsWith("file_")) {
                System.out.println("  [PASS] Test 4: Storage service created pending record " + rec.fileId);
                passed++;
            } else {
                System.out.println("  [FAIL] Test 4: Storage service record invalid");
                failed++;
            }
        } catch (Exception e) {
            System.out.println("  [FAIL] Test 4: Threw exception: " + e.getMessage());
            failed++;
        }

        System.out.println("Java Storage Suite: " + passed + " passed, " + failed + " failed.");
        if (failed > 0) {
            System.exit(1);
        }
    }
}
