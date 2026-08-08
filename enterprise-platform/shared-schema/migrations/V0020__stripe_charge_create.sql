-- Migration 0020: Create stripe_charge_create table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS stripe_charge_create (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_charge_create_status ON stripe_charge_create(status);
CREATE INDEX idx_stripe_charge_create_created_at ON stripe_charge_create(created_at);
