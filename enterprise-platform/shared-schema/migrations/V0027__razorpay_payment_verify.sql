-- Migration 0027: Create razorpay_payment_verify table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS razorpay_payment_verify (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_razorpay_payment_verify_status ON razorpay_payment_verify(status);
CREATE INDEX idx_razorpay_payment_verify_created_at ON razorpay_payment_verify(created_at);
