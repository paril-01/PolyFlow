-- Migration 0025: Create stripe_webhook_handle table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS stripe_webhook_handle (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stripe_webhook_handle_status ON stripe_webhook_handle(status);
CREATE INDEX idx_stripe_webhook_handle_created_at ON stripe_webhook_handle(created_at);
