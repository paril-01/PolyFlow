-- Migration 0033: Create coupon_apply table
-- Domain: pricing | Service: pricing-python

CREATE TABLE IF NOT EXISTS coupon_apply (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_coupon_apply_status ON coupon_apply(status);
CREATE INDEX idx_coupon_apply_created_at ON coupon_apply(created_at);
