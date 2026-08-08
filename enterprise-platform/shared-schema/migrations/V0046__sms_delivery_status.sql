-- Migration 0046: Create sms_delivery_status table
-- Domain: notifications | Service: notification-node

CREATE TABLE IF NOT EXISTS sms_delivery_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sms_delivery_status_status ON sms_delivery_status(status);
CREATE INDEX idx_sms_delivery_status_created_at ON sms_delivery_status(created_at);
