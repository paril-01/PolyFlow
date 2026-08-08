package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderDraftCreateHandler(t *testing.T) {
	h := NewOrderDraftCreateHandler()
	assert.NotNil(t, h)
}

func TestOrderDraftCreateHandle(t *testing.T) {
	h := NewOrderDraftCreateHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_draft_create", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
