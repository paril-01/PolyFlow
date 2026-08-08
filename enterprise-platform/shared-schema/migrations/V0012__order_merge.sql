-- Migration 0012: Create order_merge table
-- Domain: orders | Service: order-service-go

CREATE TABLE IF NOT EXISTS order_merge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_order_merge_status ON order_merge(status);
CREATE INDEX idx_order_merge_created_at ON order_merge(created_at);
