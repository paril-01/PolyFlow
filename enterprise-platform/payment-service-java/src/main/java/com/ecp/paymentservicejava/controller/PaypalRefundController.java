package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.PaypalRefundService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class PaypalRefundController {

    private final PaypalRefundService service;

    public PaypalRefundController(PaypalRefundService service) {
        this.service = service;
    }

    @PostMapping("/paypal-refund")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/paypal-refund/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "paypal_refund", "status", "operational"));
    }
}
