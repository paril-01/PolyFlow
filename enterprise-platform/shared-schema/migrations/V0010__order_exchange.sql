-- Migration 0010: Create order_exchange table
-- Domain: orders | Service: order-service-go

CREATE TABLE IF NOT EXISTS order_exchange (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_exchange_status ON order_exchange(status);
CREATE INDEX idx_order_exchange_created_at ON order_exchange(created_at);
