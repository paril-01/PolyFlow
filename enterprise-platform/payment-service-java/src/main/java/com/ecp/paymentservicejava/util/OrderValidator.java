package com.ecp.paymentservicejava.util;

// COPY-PASTE: This class is duplicated across services
public class OrderValidator {
    public boolean validate(String orderId) {
        return orderId != null && !orderId.isEmpty();
    }
}
