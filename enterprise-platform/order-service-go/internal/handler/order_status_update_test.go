package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderStatusUpdateHandler(t *testing.T) {
	h := NewOrderStatusUpdateHandler()
	assert.NotNil(t, h)
}

func TestOrderStatusUpdateHandle(t *testing.T) {
	h := NewOrderStatusUpdateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_status_update", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
