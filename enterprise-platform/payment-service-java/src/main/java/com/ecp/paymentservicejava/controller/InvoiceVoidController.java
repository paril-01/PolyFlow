package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.InvoiceVoidService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class InvoiceVoidController {

    private final InvoiceVoidService service;

    public InvoiceVoidController(InvoiceVoidService service) {
        this.service = service;
    }

    @PostMapping("/invoice-void")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/invoice-void/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "invoice_void", "status", "operational"));
    }
}
