-- Migration 0037: Create content_based_train table
-- Domain: recommendations | Service: recommendation-python

CREATE TABLE IF NOT EXISTS content_based_train (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_based_train_status ON content_based_train(status);
CREATE INDEX idx_content_based_train_created_at ON content_based_train(created_at);
