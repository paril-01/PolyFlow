package com.ecp.analyticsjava.buggy;

import java.util.*;

public class BugJavaMemoryLeak11 {
// BUG: static list grows unbounded
private static final List<Object> cache = new ArrayList<>();
public void process(Object item) { cache.add(item); }
}
