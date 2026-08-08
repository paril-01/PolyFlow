package handler

// DEPRECATED: This handler is no longer used. It was part of the v0 API.
// TODO: Remove in next major version (tracked in JIRA-4521)

import "net/http"

func LegacyOrdersV0Handler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"error":"deprecated endpoint"}`))
}
