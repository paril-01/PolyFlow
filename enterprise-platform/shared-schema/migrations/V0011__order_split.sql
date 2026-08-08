-- Migration 0011: Create order_split table
-- Domain: orders | Service: order-service-go

CREATE TABLE IF NOT EXISTS order_split (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_split_status ON order_split(status);
CREATE INDEX idx_order_split_created_at ON order_split(created_at);
