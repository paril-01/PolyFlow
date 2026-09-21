package com.ecp.authservicejava.buggy;

import java.util.*;

public class BugJavaNullPointer8 {
    // BUG: no null check
    public interface Item {
        double getPrice();
    }

    public interface Order {
        List<Item> getItems();
    }

    public double getTotal(Order order) {
        return order.getItems().stream().mapToDouble(Item::getPrice).sum();
    }
}
