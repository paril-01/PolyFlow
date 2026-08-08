-- Migration 0050: Create funnel_define table
-- Domain: analytics | Service: analytics-java

CREATE TABLE IF NOT EXISTS funnel_define (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funnel_define_status ON funnel_define(status);
CREATE INDEX idx_funnel_define_created_at ON funnel_define(created_at);
