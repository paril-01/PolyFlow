package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.SettlementWeeklyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class SettlementWeeklyController {

    private final SettlementWeeklyService service;

    public SettlementWeeklyController(SettlementWeeklyService service) {
        this.service = service;
    }

    @PostMapping("/settlement-weekly")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/settlement-weekly/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "settlement_weekly", "status", "operational"));
    }
}
