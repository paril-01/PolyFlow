package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.StripeChargeRefundService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class StripeChargeRefundController {

    private final StripeChargeRefundService service;

    public StripeChargeRefundController(StripeChargeRefundService service) {
        this.service = service;
    }

    @PostMapping("/stripe-charge-refund")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/stripe-charge-refund/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "stripe_charge_refund", "status", "operational"));
    }
}
