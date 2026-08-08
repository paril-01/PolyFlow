-- Migration 0009: Create order_return_approve table
-- Domain: orders | Service: order-service-go

CREATE TABLE IF NOT EXISTS order_return_approve (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_return_approve_status ON order_return_approve(status);
CREATE INDEX idx_order_return_approve_created_at ON order_return_approve(created_at);
