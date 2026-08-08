-- Migration 0036: Create collab_filter_retrain table
-- Domain: recommendations | Service: recommendation-python

CREATE TABLE IF NOT EXISTS collab_filter_retrain (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_collab_filter_retrain_status ON collab_filter_retrain(status);
CREATE INDEX idx_collab_filter_retrain_created_at ON collab_filter_retrain(created_at);
