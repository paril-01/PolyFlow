package com.ecp.authservicejava.buggy;

import java.util.*;

public class BugJavaDeadlock9 {
// BUG: lock ordering deadlock
synchronized(lockA) { synchronized(lockB) { transfer(); } }
}
