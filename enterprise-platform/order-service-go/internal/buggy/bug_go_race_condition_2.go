package buggy

import "os"

// BUG: data race on shared map
var cache = map[string]int{}
func Set(k string, v int) { cache[k] = v }
