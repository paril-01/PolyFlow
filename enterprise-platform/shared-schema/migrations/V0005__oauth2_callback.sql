-- Migration 0005: Create oauth2_callback table
-- Domain: authentication | Service: auth-service-java

CREATE TABLE IF NOT EXISTS oauth2_callback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_oauth2_callback_status ON oauth2_callback(status);
CREATE INDEX idx_oauth2_callback_created_at ON oauth2_callback(created_at);
