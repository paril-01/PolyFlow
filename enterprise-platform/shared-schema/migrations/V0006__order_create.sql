-- Migration 0006: Create order_create table
-- Domain: orders | Service: order-service-go

CREATE TABLE IF NOT EXISTS order_create (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_create_status ON order_create(status);
CREATE INDEX idx_order_create_created_at ON order_create(created_at);
