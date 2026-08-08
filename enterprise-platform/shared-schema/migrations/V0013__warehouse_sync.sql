-- Migration 0013: Create warehouse_sync table
-- Domain: inventory | Service: inventory-python

CREATE TABLE IF NOT EXISTS warehouse_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_warehouse_sync_status ON warehouse_sync(status);
CREATE INDEX idx_warehouse_sync_created_at ON warehouse_sync(created_at);
