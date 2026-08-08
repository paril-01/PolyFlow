package com.ecp.analyticsjava.buggy;

import java.util.*;

public class BugJavaDeadlock14 {
// BUG: lock ordering deadlock
synchronized(lockA) { synchronized(lockB) { transfer(); } }
}
