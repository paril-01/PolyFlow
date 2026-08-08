-- Migration 0026: Create razorpay_order_create table
-- Domain: payments | Service: payment-service-java

CREATE TABLE IF NOT EXISTS razorpay_order_create (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_razorpay_order_create_status ON razorpay_order_create(status);
CREATE INDEX idx_razorpay_order_create_created_at ON razorpay_order_create(created_at);
