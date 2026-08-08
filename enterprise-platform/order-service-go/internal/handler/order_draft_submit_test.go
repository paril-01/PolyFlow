package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderDraftSubmitHandler(t *testing.T) {
	h := NewOrderDraftSubmitHandler()
	assert.NotNil(t, h)
}

func TestOrderDraftSubmitHandle(t *testing.T) {
	h := NewOrderDraftSubmitHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_draft_submit", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
