package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderShippingTrackHandler(t *testing.T) {
	h := NewOrderShippingTrackHandler()
	assert.NotNil(t, h)
}

func TestOrderShippingTrackHandle(t *testing.T) {
	h := NewOrderShippingTrackHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_shipping_track", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
