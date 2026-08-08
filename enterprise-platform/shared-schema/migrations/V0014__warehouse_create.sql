-- Migration 0014: Create warehouse_create table
-- Domain: inventory | Service: inventory-python

CREATE TABLE IF NOT EXISTS warehouse_create (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_warehouse_create_status ON warehouse_create(status);
CREATE INDEX idx_warehouse_create_created_at ON warehouse_create(created_at);
