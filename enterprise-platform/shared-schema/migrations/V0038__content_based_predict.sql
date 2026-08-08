-- Migration 0038: Create content_based_predict table
-- Domain: recommendations | Service: recommendation-python

CREATE TABLE IF NOT EXISTS content_based_predict (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_based_predict_status ON content_based_predict(status);
CREATE INDEX idx_content_based_predict_created_at ON content_based_predict(created_at);
