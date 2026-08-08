-- Migration 0021: Create stripe_charge_capture table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS stripe_charge_capture (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_charge_capture_status ON stripe_charge_capture(status);
CREATE INDEX idx_stripe_charge_capture_created_at ON stripe_charge_capture(created_at);
