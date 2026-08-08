package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderShippingUpdateHandler(t *testing.T) {
	h := NewOrderShippingUpdateHandler()
	assert.NotNil(t, h)
}

func TestOrderShippingUpdateHandle(t *testing.T) {
	h := NewOrderShippingUpdateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_shipping_update", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
