-- Migration 0028: Create price_base_set table
-- Domain: pricing | Service: pricing-python

CREATE TABLE IF NOT EXISTS price_base_set (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_base_set_status ON price_base_set(status);
CREATE INDEX idx_price_base_set_created_at ON price_base_set(created_at);
