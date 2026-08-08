package com.ecp.paymentservicejava.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import java.util.Map;

class StripeWebhookHandleServiceTest {

    private StripeWebhookHandleService service;

    @BeforeEach
    void setUp() {
        service = new StripeWebhookHandleService();
    }

    @Test
    void testExecuteSuccess() {
        Map<String, Object> result = service.execute(Map.of("test", "value"));
        assertEquals("success", result.get("status"));
        assertNotNull(result.get("trace_id"));
    }

    @Test
    void testExecuteEmptyRequest() {
        Map<String, Object> result = service.execute(Map.of());
        assertEquals("success", result.get("status"));
    }
}
