package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.RazorpayPaymentVerifyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class RazorpayPaymentVerifyController {

    private final RazorpayPaymentVerifyService service;

    public RazorpayPaymentVerifyController(RazorpayPaymentVerifyService service) {
        this.service = service;
    }

    @PostMapping("/razorpay-payment-verify")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/razorpay-payment-verify/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "razorpay_payment_verify", "status", "operational"));
    }
}
