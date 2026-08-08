package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.RbacRoleCreateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class RbacRoleCreateController {

    private final RbacRoleCreateService service;

    public RbacRoleCreateController(RbacRoleCreateService service) {
        this.service = service;
    }

    @PostMapping("/rbac-role-create")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/rbac-role-create/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "rbac_role_create", "status", "operational"));
    }
}
