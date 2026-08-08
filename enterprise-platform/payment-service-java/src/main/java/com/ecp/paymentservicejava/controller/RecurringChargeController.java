package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RecurringChargeService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RecurringChargeController {

    private final RecurringChargeService service;

    public RecurringChargeController(RecurringChargeService service) {
        this.service = service;
    }

    @PostMapping("/recurring-charge")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/recurring-charge/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "recurring_charge", "status", "operational"));
    }
}
