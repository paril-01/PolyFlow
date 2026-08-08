package com.ecp.authservicejava.controller;

import com.ecp.authservicejava.service.Oauth2CallbackService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/authentication")
public class Oauth2CallbackController {

    private final Oauth2CallbackService service;

    public Oauth2CallbackController(Oauth2CallbackService service) {
        this.service = service;
    }

    @PostMapping("/oauth2-callback")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/oauth2-callback/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "oauth2_callback", "status", "operational"));
    }
}
