-- Migration 0034: Create collab_filter_train table
-- Domain: recommendations | Service: recommendation-python

CREATE TABLE IF NOT EXISTS collab_filter_train (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_collab_filter_train_status ON collab_filter_train(status);
CREATE INDEX idx_collab_filter_train_created_at ON collab_filter_train(created_at);
