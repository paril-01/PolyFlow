package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.InvoiceCreateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class InvoiceCreateController {

    private final InvoiceCreateService service;

    public InvoiceCreateController(InvoiceCreateService service) {
        this.service = service;
    }

    @PostMapping("/invoice-create")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/invoice-create/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "invoice_create", "status", "operational"));
    }
}
