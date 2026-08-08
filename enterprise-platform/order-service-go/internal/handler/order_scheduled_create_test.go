package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderScheduledCreateHandler(t *testing.T) {
	h := NewOrderScheduledCreateHandler()
	assert.NotNil(t, h)
}

func TestOrderScheduledCreateHandle(t *testing.T) {
	h := NewOrderScheduledCreateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_scheduled_create", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
