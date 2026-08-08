package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.Oauth2PkceFlowService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class Oauth2PkceFlowController {

    private final Oauth2PkceFlowService service;

    public Oauth2PkceFlowController(Oauth2PkceFlowService service) {
        this.service = service;
    }

    @PostMapping("/oauth2-pkce-flow")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/oauth2-pkce-flow/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "oauth2_pkce_flow", "status", "operational"));
    }
}
