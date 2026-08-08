-- Migration 0047: Create revenue_dashboard_compute table
-- Domain: analytics | Service: analytics-java

CREATE TABLE IF NOT EXISTS revenue_dashboard_compute (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_revenue_dashboard_compute_status ON revenue_dashboard_compute(status);
CREATE INDEX idx_revenue_dashboard_compute_created_at ON revenue_dashboard_compute(created_at);
