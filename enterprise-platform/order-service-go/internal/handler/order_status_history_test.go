package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderStatusHistoryHandler(t *testing.T) {
	h := NewOrderStatusHistoryHandler()
	assert.NotNil(t, h)
}

func TestOrderStatusHistoryHandle(t *testing.T) {
	h := NewOrderStatusHistoryHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_status_history", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
