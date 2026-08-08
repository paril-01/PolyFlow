package buggy

import "os"

// BUG: error ignored
func readFile(path string) []byte {
	data, _ := os.ReadFile(path)
	return data
}
