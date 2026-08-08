-- Migration 0022: Create stripe_charge_refund table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS stripe_charge_refund (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_charge_refund_status ON stripe_charge_refund(status);
CREATE INDEX idx_stripe_charge_refund_created_at ON stripe_charge_refund(created_at);
