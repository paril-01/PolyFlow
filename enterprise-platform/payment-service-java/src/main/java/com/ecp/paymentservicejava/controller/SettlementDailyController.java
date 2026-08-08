package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.SettlementDailyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class SettlementDailyController {

    private final SettlementDailyService service;

    public SettlementDailyController(SettlementDailyService service) {
        this.service = service;
    }

    @PostMapping("/settlement-daily")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/settlement-daily/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "settlement_daily", "status", "operational"));
    }
}
