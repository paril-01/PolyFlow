-- Migration 0044: Create sms_send table
-- Domain: notifications | Service: notification-node

CREATE TABLE IF NOT EXISTS sms_send (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sms_send_status ON sms_send(status);
CREATE INDEX idx_sms_send_created_at ON sms_send(created_at);
