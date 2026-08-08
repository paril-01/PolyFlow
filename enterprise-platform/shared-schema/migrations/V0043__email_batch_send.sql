-- Migration 0043: Create email_batch_send table
-- Domain: notifications | Service: notification-node

CREATE TABLE IF NOT EXISTS email_batch_send (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_email_batch_send_status ON email_batch_send(status);
CREATE INDEX idx_email_batch_send_created_at ON email_batch_send(created_at);
