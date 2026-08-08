-- DUPLICATE: This migration creates an index that already exists in V0003
CREATE INDEX IF NOT EXISTS idx_order_create_status ON order_create(status);
