package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.RbacPermissionCheckService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class RbacPermissionCheckController {

    private final RbacPermissionCheckService service;

    public RbacPermissionCheckController(RbacPermissionCheckService service) {
        this.service = service;
    }

    @PostMapping("/rbac-permission-check")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/rbac-permission-check/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "rbac_permission_check", "status", "operational"));
    }
}
