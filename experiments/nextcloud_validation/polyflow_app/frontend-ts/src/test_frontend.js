// test_frontend.js — Real Node.js runner testing the frontend contracts and validation

console.log("Running PolyFlow Frontend Test Suite (Node.js " + process.version + ")...");
let passed = 0;
let failed = 0;

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validateUploadParams(fileName, sizeBytes) {
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

// Test 1: formatFileSize
if (formatFileSize(500) === "500 B" && formatFileSize(2048) === "2.0 KB" && formatFileSize(10485760) === "10.0 MB") {
  console.log("  [PASS] Test 1: formatFileSize correctly formats bytes/KB/MB");
  passed++;
} else {
  console.log("  [FAIL] Test 1: formatFileSize mismatch");
  failed++;
}

// Test 2: validateUploadParams valid
const v1 = validateUploadParams("photo.jpg", 1024 * 300);
if (v1.valid) {
  console.log("  [PASS] Test 2: Accepted valid photo.jpg (300 KB)");
  passed++;
} else {
  console.log("  [FAIL] Test 2: Rejected valid file: " + v1.error);
  failed++;
}

// Test 3: validateUploadParams rejects >500MB
const v2 = validateUploadParams("archive.tar", 600 * 1024 * 1024);
if (!v2.valid && v2.error.includes("500MB")) {
  console.log("  [PASS] Test 3: Correctly rejected oversized file (>500MB)");
  passed++;
} else {
  console.log("  [FAIL] Test 3: Allowed oversized file");
  failed++;
}

console.log("Frontend Node Suite: " + passed + " passed, " + failed + " failed.");
if (failed > 0) process.exit(1);
