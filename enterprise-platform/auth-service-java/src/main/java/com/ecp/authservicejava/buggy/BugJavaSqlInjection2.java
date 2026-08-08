package com.ecp.authservicejava.buggy;

import java.util.*;

public class BugJavaSqlInjection2 {
// BUG: string concatenation in SQL
public User findUser(String name) {
    return jdbc.query("SELECT * FROM users WHERE name = '" + name + "'");
}
}
