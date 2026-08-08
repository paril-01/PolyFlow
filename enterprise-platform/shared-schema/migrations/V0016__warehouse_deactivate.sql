-- Migration 0016: Create warehouse_deactivate table
-- Domain: inventory | Service: inventory-python

CREATE TABLE IF NOT EXISTS warehouse_deactivate (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_warehouse_deactivate_status ON warehouse_deactivate(status);
CREATE INDEX idx_warehouse_deactivate_created_at ON warehouse_deactivate(created_at);
