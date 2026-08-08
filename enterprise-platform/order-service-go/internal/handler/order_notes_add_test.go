package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestNewOrderNotesAddHandler(t *testing.T) {
	h := NewOrderNotesAddHandler()
	assert.NotNil(t, h)
}

func TestOrderNotesAddHandle(t *testing.T) {
	h := NewOrderNotesAddHandler()
	body, _ := json.Marshal(map[string]interface{}{"test": true})
	req := httptest.NewRequest(http.MethodPost, "/order_notes_add", bytes.NewBuffer(body))
	rec := httptest.NewRecorder()
	h.Handle(rec, req)
	assert.Equal(t, http.StatusOK, rec.Code)
}
