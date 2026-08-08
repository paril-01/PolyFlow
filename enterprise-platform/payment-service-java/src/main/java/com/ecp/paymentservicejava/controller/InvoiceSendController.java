package com.ecp.paymentservicejava.controller;

import com.ecp.paymentservicejava.service.InvoiceSendService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/payments")
public class InvoiceSendController {

    private final InvoiceSendService service;

    public InvoiceSendController(InvoiceSendService service) {
        this.service = service;
    }

    @PostMapping("/invoice-send")
    public ResponseEntity<Map<String, Object>> handle(@RequestBody Map<String, Object> request) {
        Map<String, Object> result = service.execute(request);
        return ResponseEntity.ok(result);
    }

    @GetMapping("/invoice-send/status")
    public ResponseEntity<Map<String, Object>> status() {
        return ResponseEntity.ok(Map.of("feature", "invoice_send", "status", "operational"));
    }
}
