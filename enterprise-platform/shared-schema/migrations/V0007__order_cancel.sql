-- Migration 0007: Create order_cancel table
-- Domain: orders | Service: order-service-go

CREATE TABLE IF NOT EXISTS order_cancel (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_cancel_status ON order_cancel(status);
CREATE INDEX idx_order_cancel_created_at ON order_cancel(created_at);
