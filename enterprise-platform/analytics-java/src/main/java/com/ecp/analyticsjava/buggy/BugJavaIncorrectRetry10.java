package com.ecp.analyticsjava.buggy;

import java.util.*;

public class BugJavaIncorrectRetry10 {
// BUG: retrying non-idempotent operation
public void chargeCard() {
    for (int i = 0; i < 3; i++) {
        try { stripe.charge(); break; } catch (Exception e) { /* retry */ }
    }
}
}
