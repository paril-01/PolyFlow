package com.ecp.analyticsjava.buggy;

import java.util.*;

public class BugJavaIncorrectRetry15 {
    // BUG: retrying non-idempotent operation
    interface StripeClient {
        void charge() throws Exception;
    }

    private StripeClient stripe;

    public void chargeCard() {
        for (int i = 0; i < 3; i++) {
            try { stripe.charge(); break; } catch (Exception e) { /* retry */ }
        }
    }
}
