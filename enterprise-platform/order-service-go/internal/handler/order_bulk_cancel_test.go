package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderBulkCancelHandler(t *testing.T) {
	h := NewOrderBulkCancelHandler()
	assert.NotNil(t, h)
}

func TestOrderBulkCancelHandle(t *testing.T) {
	h := NewOrderBulkCancelHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_bulk_cancel", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
