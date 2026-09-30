package polyflow.storage;

public class PermissionChecker {
    public static boolean hasAccess(String userRole, String grantPermission, String requiredAction) {
        if ("admin".equalsIgnoreCase(userRole)) return true;
        if ("ADMIN".equalsIgnoreCase(grantPermission)) return true;
        if ("WRITE".equalsIgnoreCase(grantPermission)) {
            return "READ".equalsIgnoreCase(requiredAction) || "WRITE".equalsIgnoreCase(requiredAction);
        }
        if ("READ".equalsIgnoreCase(grantPermission)) {
            return "READ".equalsIgnoreCase(requiredAction);
        }
        return false;
    }
}
