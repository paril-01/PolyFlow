package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderReturnRequestHandler(t *testing.T) {
	h := NewOrderReturnRequestHandler()
	assert.NotNil(t, h)
}

func TestOrderReturnRequestHandle(t *testing.T) {
	h := NewOrderReturnRequestHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_return_request", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
