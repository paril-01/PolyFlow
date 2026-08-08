package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.RbacRoleAssignService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class RbacRoleAssignController {

    private final RbacRoleAssignService service;

    public RbacRoleAssignController(RbacRoleAssignService service) {
        this.service = service;
    }

    @PostMapping("/rbac-role-assign")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/rbac-role-assign/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "rbac_role_assign", "status", "operational"));
    }
}
