package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderTaxCalculateHandler(t *testing.T) {
	h := NewOrderTaxCalculateHandler()
	assert.NotNil(t, h)
}

func TestOrderTaxCalculateHandle(t *testing.T) {
	h := NewOrderTaxCalculateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_tax_calculate", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
