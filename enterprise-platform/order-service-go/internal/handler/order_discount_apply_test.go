package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderDiscountApplyHandler(t *testing.T) {
	h := NewOrderDiscountApplyHandler()
	assert.NotNil(t, h)
}

func TestOrderDiscountApplyHandle(t *testing.T) {
	h := NewOrderDiscountApplyHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_discount_apply", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
