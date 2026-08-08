package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderScheduledProcessHandler(t *testing.T) {
	h := NewOrderScheduledProcessHandler()
	assert.NotNil(t, h)
}

func TestOrderScheduledProcessHandle(t *testing.T) {
	h := NewOrderScheduledProcessHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_scheduled_process", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
