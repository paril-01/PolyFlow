-- Migration 0051: Create funnel_compute table
-- Domain: analytics | Service: analytics-java

CREATE TABLE IF NOT EXISTS funnel_compute (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funnel_compute_status ON funnel_compute(status);
CREATE INDEX idx_funnel_compute_created_at ON funnel_compute(created_at);
