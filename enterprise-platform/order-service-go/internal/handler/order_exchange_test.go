package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderExchangeHandler(t *testing.T) {
	h := NewOrderExchangeHandler()
	assert.NotNil(t, h)
}

func TestOrderExchangeHandle(t *testing.T) {
	h := NewOrderExchangeHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_exchange", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
