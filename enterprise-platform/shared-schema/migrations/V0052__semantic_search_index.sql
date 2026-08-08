-- Migration 0052: Create semantic_search_index table
-- Domain: ai_features | Service: ai-service-python

CREATE TABLE IF NOT EXISTS semantic_search_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_semantic_search_index_status ON semantic_search_index(status);
CREATE INDEX idx_semantic_search_index_created_at ON semantic_search_index(created_at);
