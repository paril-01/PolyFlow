package model

import (
	"time"
	"github.com/google/uuid"
)

// OrderDiscountApply represents the data model for Order Discount Apply.
type OrderDiscountApply struct {
	ID        uuid.UUID              `json:"id" db:"id"`
	Status    string                 `json:"status" db:"status"`
	Payload   map[string]interface{} `json:"payload"`
	CreatedAt time.Time              `json:"created_at" db:"created_at"`
	UpdatedAt time.Time              `json:"updated_at" db:"updated_at"`
}
