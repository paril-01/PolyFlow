-- Migration 0002: Create jwt_token_verify table
-- Domain: authentication | Service: auth-service-java

CREATE TABLE IF NOT EXISTS jwt_token_verify (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jwt_token_verify_status ON jwt_token_verify(status);
CREATE INDEX idx_jwt_token_verify_created_at ON jwt_token_verify(created_at);
