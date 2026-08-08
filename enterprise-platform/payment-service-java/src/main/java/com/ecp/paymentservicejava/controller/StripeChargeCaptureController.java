package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.StripeChargeCaptureService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class StripeChargeCaptureController {

    private final StripeChargeCaptureService service;

    public StripeChargeCaptureController(StripeChargeCaptureService service) {
        this.service = service;
    }

    @PostMapping("/stripe-charge-capture")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/stripe-charge-capture/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "stripe_charge_capture", "status", "operational"));
    }
}
