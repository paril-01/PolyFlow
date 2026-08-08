-- Migration 0039: Create trending_compute_hourly table
-- Domain: recommendations | Service: recommendation-python

CREATE TABLE IF NOT EXISTS trending_compute_hourly (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_trending_compute_hourly_status ON trending_compute_hourly(status);
CREATE INDEX idx_trending_compute_hourly_created_at ON trending_compute_hourly(created_at);
