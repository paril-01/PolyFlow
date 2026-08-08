-- Migration 0004: Create oauth2_pkce_flow table
-- Domain: authentication | Service: auth-service-java

CREATE TABLE IF NOT EXISTS oauth2_pkce_flow (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_oauth2_pkce_flow_status ON oauth2_pkce_flow(status);
CREATE INDEX idx_oauth2_pkce_flow_created_at ON oauth2_pkce_flow(created_at);
