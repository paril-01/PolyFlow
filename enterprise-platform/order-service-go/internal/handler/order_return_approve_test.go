package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderReturnApproveHandler(t *testing.T) {
	h := NewOrderReturnApproveHandler()
	assert.NotNil(t, h)
}

func TestOrderReturnApproveHandle(t *testing.T) {
	h := NewOrderReturnApproveHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_return_approve", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
