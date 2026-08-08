package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.PaypalOrderCreateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class PaypalOrderCreateController {

    private final PaypalOrderCreateService service;

    public PaypalOrderCreateController(PaypalOrderCreateService service) {
        this.service = service;
    }

    @PostMapping("/paypal-order-create")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/paypal-order-create/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "paypal_order_create", "status", "operational"));
    }
}
