-- Migration 0049: Create revenue_by_region table
-- Domain: analytics | Service: analytics-java

CREATE TABLE IF NOT EXISTS revenue_by_region (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_revenue_by_region_status ON revenue_by_region(status);
CREATE INDEX idx_revenue_by_region_created_at ON revenue_by_region(created_at);
