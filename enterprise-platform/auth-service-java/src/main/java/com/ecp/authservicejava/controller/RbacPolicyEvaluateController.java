package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.RbacPolicyEvaluateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class RbacPolicyEvaluateController {

    private final RbacPolicyEvaluateService service;

    public RbacPolicyEvaluateController(RbacPolicyEvaluateService service) {
        this.service = service;
    }

    @PostMapping("/rbac-policy-evaluate")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/rbac-policy-evaluate/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "rbac_policy_evaluate", "status", "operational"));
    }
}
