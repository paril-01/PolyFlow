-- Migration 0032: Create coupon_validate table
-- Domain: pricing | Service: pricing-python

CREATE TABLE IF NOT EXISTS coupon_validate (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_coupon_validate_status ON coupon_validate(status);
CREATE INDEX idx_coupon_validate_created_at ON coupon_validate(created_at);
