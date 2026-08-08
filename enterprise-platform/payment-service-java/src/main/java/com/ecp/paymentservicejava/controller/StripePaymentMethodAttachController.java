package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.StripePaymentMethodAttachService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class StripePaymentMethodAttachController {

    private final StripePaymentMethodAttachService service;

    public StripePaymentMethodAttachController(StripePaymentMethodAttachService service) {
        this.service = service;
    }

    @PostMapping("/stripe-payment-method-attach")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/stripe-payment-method-attach/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "stripe_payment_method_attach", "status", "operational"));
    }
}
