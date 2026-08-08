-- Migration 0019: Create stock_low_alert table
-- Domain: inventory | Service: inventory-python

CREATE TABLE IF NOT EXISTS stock_low_alert (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    payload JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stock_low_alert_status ON stock_low_alert(status);
CREATE INDEX idx_stock_low_alert_created_at ON stock_low_alert(created_at);
