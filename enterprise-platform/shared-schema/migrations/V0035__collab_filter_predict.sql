-- Migration 0035: Create collab_filter_predict table
-- Domain: recommendations | Service: recommendation-python

CREATE TABLE IF NOT EXISTS collab_filter_predict (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_collab_filter_predict_status ON collab_filter_predict(status);
CREATE INDEX idx_collab_filter_predict_created_at ON collab_filter_predict(created_at);
