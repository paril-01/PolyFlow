package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderBulkCreateHandler(t *testing.T) {
	h := NewOrderBulkCreateHandler()
	assert.NotNil(t, h)
}

func TestOrderBulkCreateHandle(t *testing.T) {
	h := NewOrderBulkCreateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_bulk_create", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
