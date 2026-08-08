-- Migration 0030: Create price_surge_detect table
-- Domain: pricing | Service: pricing-python

CREATE TABLE IF NOT EXISTS price_surge_detect (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_price_surge_detect_status ON price_surge_detect(status);
CREATE INDEX idx_price_surge_detect_created_at ON price_surge_detect(created_at);
