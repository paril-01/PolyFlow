package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.JwtTokenIssueService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class JwtTokenIssueController {

    private final JwtTokenIssueService service;

    public JwtTokenIssueController(JwtTokenIssueService service) {
        this.service = service;
    }

    @PostMapping("/jwt-token-issue")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/jwt-token-issue/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "jwt_token_issue", "status", "operational"));
    }
}
