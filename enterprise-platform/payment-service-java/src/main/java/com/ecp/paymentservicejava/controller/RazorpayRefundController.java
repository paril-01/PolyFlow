package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RazorpayRefundService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RazorpayRefundController {

    private final RazorpayRefundService service;

    public RazorpayRefundController(RazorpayRefundService service) {
        this.service = service;
    }

    @PostMapping("/razorpay-refund")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/razorpay-refund/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "razorpay_refund", "status", "operational"));
    }
}
