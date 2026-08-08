-- Migration 0018: Create stock_level_update table
-- Domain: inventory | Service: inventory-python

CREATE TABLE IF NOT EXISTS stock_level_update (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stock_level_update_status ON stock_level_update(status);
CREATE INDEX idx_stock_level_update_created_at ON stock_level_update(created_at);
