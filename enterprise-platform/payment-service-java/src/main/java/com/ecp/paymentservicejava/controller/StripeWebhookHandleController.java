package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.StripeWebhookHandleService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class StripeWebhookHandleController {

    private final StripeWebhookHandleService service;

    public StripeWebhookHandleController(StripeWebhookHandleService service) {
        this.service = service;
    }

    @PostMapping("/stripe-webhook-handle")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/stripe-webhook-handle/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "stripe_webhook_handle", "status", "operational"));
    }
}
