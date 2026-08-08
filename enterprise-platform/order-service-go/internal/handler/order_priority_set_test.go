package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderPrioritySetHandler(t *testing.T) {
	h := NewOrderPrioritySetHandler()
	assert.NotNil(t, h)
}

func TestOrderPrioritySetHandle(t *testing.T) {
	h := NewOrderPrioritySetHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_priority_set", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
