-- Migration 0057: Create review_keyword_extract table
-- Domain: ai_features | Service: ai-service-python

CREATE TABLE IF NOT EXISTS review_keyword_extract (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_review_keyword_extract_status ON review_keyword_extract(status);
CREATE INDEX idx_review_keyword_extract_created_at ON review_keyword_extract(created_at);
