-- Migration 0031: Create coupon_create table
-- Domain: pricing | Service: pricing-python

CREATE TABLE IF NOT EXISTS coupon_create (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_coupon_create_status ON coupon_create(status);
CREATE INDEX idx_coupon_create_created_at ON coupon_create(created_at);
