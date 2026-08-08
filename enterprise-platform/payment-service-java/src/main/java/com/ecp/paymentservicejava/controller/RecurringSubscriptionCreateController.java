package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RecurringSubscriptionCreateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RecurringSubscriptionCreateController {

    private final RecurringSubscriptionCreateService service;

    public RecurringSubscriptionCreateController(RecurringSubscriptionCreateService service) {
        this.service = service;
    }

    @PostMapping("/recurring-subscription-create")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/recurring-subscription-create/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "recurring_subscription_create", "status", "operational"));
    }
}
