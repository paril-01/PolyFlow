package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.PaypalCaptureService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class PaypalCaptureController {

    private final PaypalCaptureService service;

    public PaypalCaptureController(PaypalCaptureService service) {
        this.service = service;
    }

    @PostMapping("/paypal-capture")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/paypal-capture/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "paypal_capture", "status", "operational"));
    }
}
