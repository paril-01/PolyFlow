package handler

import (
	"encoding/json"
	"net/http"
	"time"
	"github.com/google/uuid"
	"github.com/rs/zerolog/log"
)

// OrderSubtotalComputeHandler handles Order Subtotal Compute requests.
type OrderSubtotalComputeHandler struct {
	// Dependencies injected here
}

// NewOrderSubtotalComputeHandler creates a new handler instance.
func NewOrderSubtotalComputeHandler() *OrderSubtotalComputeHandler {
	return &OrderSubtotalComputeHandler{}
}

// Handle processes Order Subtotal Compute requests.
func (h *OrderSubtotalComputeHandler) Handle(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	traceID := uuid.New().String()[:8]
	log.Info().Str("trace_id", traceID).Msg("Processing order_subtotal_compute")

	var req map[string]interface{}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"invalid request"}`, http.StatusBadRequest)
		return
	}

	result := h.process(req)
	elapsed := time.Since(start).Milliseconds()

	resp := map[string]interface{}{
		"status":           "success",
		"trace_id":         traceID,
		"result":           result,
		"processing_ms":    elapsed,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *OrderSubtotalComputeHandler) process(req map[string]interface{}) map[string]interface{} {
	return map[string]interface{}{
		"feature": "order_subtotal_compute",
		"domain":  "orders",
		"processed": true,
	}
}
