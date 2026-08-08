-- Migration 0056: Create review_sentiment_analyze table
-- Domain: ai_features | Service: ai-service-python

CREATE TABLE IF NOT EXISTS review_sentiment_analyze (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_review_sentiment_analyze_status ON review_sentiment_analyze(status);
CREATE INDEX idx_review_sentiment_analyze_created_at ON review_sentiment_analyze(created_at);
