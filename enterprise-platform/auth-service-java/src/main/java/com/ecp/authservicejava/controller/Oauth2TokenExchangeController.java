package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.Oauth2TokenExchangeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class Oauth2TokenExchangeController {

    private final Oauth2TokenExchangeService service;

    public Oauth2TokenExchangeController(Oauth2TokenExchangeService service) {
        this.service = service;
    }

    @PostMapping("/oauth2-token-exchange")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/oauth2-token-exchange/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "oauth2_token_exchange", "status", "operational"));
    }
}
