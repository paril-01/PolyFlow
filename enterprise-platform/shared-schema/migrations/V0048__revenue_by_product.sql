-- Migration 0048: Create revenue_by_product table
-- Domain: analytics | Service: analytics-java

CREATE TABLE IF NOT EXISTS revenue_by_product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_revenue_by_product_status ON revenue_by_product(status);
CREATE INDEX idx_revenue_by_product_created_at ON revenue_by_product(created_at);
