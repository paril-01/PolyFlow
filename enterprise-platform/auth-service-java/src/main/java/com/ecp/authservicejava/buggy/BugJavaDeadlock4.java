package com.ecp.authservicejava.buggy;

import java.util.*;

public class BugJavaDeadlock4 {
    // BUG: lock ordering deadlock
    private final Object lockA = new Object();
    private final Object lockB = new Object();

    public void transferMoney() {
        synchronized (lockA) {
            synchronized (lockB) {
                transfer();
            }
        }
    }

    private void transfer() {}
}
