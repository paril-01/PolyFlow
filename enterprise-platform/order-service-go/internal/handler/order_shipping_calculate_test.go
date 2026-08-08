package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderShippingCalculateHandler(t *testing.T) {
	h := NewOrderShippingCalculateHandler()
	assert.NotNil(t, h)
}

func TestOrderShippingCalculateHandle(t *testing.T) {
	h := NewOrderShippingCalculateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_shipping_calculate", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
