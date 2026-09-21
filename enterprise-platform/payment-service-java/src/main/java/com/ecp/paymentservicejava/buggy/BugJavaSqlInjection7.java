package com.ecp.paymentservicejava.buggy;

import java.util.*;

public class BugJavaSqlInjection7 {
    // BUG: string concatenation in SQL
    public static class User {}

    public interface JdbcTemplate {
        User query(String sql);
    }

    private JdbcTemplate jdbc;

    public User findUser(String name) {
        return jdbc.query("SELECT * FROM users WHERE name = '" + name + "'");
    }
}
