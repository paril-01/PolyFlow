-- Migration 0024: Create stripe_payment_method_attach table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS stripe_payment_method_attach (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_payment_method_attach_status ON stripe_payment_method_attach(status);
CREATE INDEX idx_stripe_payment_method_attach_created_at ON stripe_payment_method_attach(created_at);
