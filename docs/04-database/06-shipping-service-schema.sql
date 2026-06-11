-- Shipping Service schema (PostgreSQL)
CREATE TABLE shipments (
  id BIGSERIAL PRIMARY KEY,
  tracking_number VARCHAR(50) NOT NULL UNIQUE,
  order_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  carrier VARCHAR(20) NOT NULL DEFAULT 'ghn',
  service_type VARCHAR(20) NOT NULL DEFAULT 'standard',
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  recipient_name VARCHAR(255) NOT NULL,
  recipient_phone VARCHAR(20) NOT NULL,
  origin_address JSONB NOT NULL DEFAULT '{}',
  destination_address JSONB NOT NULL DEFAULT '{}',
  shipping_fee NUMERIC(12,2) NOT NULL DEFAULT 0,
  weight_kg NUMERIC(8,2) NOT NULL DEFAULT 0,
  estimated_delivery TIMESTAMPTZ NULL,
  shipped_at TIMESTAMPTZ NULL,
  delivered_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_shipments_order_id ON shipments(order_id);
CREATE INDEX idx_shipments_user_id ON shipments(user_id);

CREATE TABLE shipment_tracking (
  id BIGSERIAL PRIMARY KEY,
  shipment_id BIGINT NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL,
  location VARCHAR(255) NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  recorded_at TIMESTAMPTZ NOT NULL
);
