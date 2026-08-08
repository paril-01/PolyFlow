-- Migration 0029: Create price_dynamic_compute table
-- Domain: pricing | Service: pricing-python

CREATE TABLE IF NOT EXISTS price_dynamic_compute (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_dynamic_compute_status ON price_dynamic_compute(status);
CREATE INDEX idx_price_dynamic_compute_created_at ON price_dynamic_compute(created_at);
