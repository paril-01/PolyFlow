-- Migration 0015: Create warehouse_update table
-- Domain: inventory | Service: inventory-python

CREATE TABLE IF NOT EXISTS warehouse_update (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_warehouse_update_status ON warehouse_update(status);
CREATE INDEX idx_warehouse_update_created_at ON warehouse_update(created_at);
