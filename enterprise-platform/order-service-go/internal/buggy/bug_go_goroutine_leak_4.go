package buggy

import "os"

// BUG: goroutine leak - channel never read
func process() {
	ch := make(chan int)
	go func() { ch <- 42 }()
	// ch is never read
}
