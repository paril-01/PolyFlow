package com.ecp.authservicejava.buggy;

import java.util.*;

public class BugJavaNullPointer8 {
// BUG: no null check
public double getTotal(Order order) {
    return order.getItems().stream().mapToDouble(Item::getPrice).sum();
}
}
