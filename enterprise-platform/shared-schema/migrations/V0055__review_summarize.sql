-- Migration 0055: Create review_summarize table
-- Domain: ai_features | Service: ai-service-python

CREATE TABLE IF NOT EXISTS review_summarize (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_review_summarize_status ON review_summarize(status);
CREATE INDEX idx_review_summarize_created_at ON review_summarize(created_at);
