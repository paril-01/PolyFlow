-- Migration 0045: Create sms_template_render table
-- Domain: notifications | Service: notification-node

CREATE TABLE IF NOT EXISTS sms_template_render (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sms_template_render_status ON sms_template_render(status);
CREATE INDEX idx_sms_template_render_created_at ON sms_template_render(created_at);
