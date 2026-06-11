-- Order Service schema (PostgreSQL)
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  order_number UUID NOT NULL UNIQUE,
  user_id INTEGER NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  subtotal NUMERIC(14,2) NOT NULL DEFAULT 0,
  shipping_fee NUMERIC(12,2) NOT NULL DEFAULT 0,
  discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
  total_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
  shipping_address JSONB NOT NULL DEFAULT '{}',
  payment_method VARCHAR(50) NOT NULL,
  payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  notes TEXT NOT NULL DEFAULT '',
  ordered_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_orders_user_id ON orders(user_id);

CREATE TABLE order_items (
  id BIGSERIAL PRIMARY KEY,
  order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL,
  product_name VARCHAR(255) NOT NULL,
  product_sku VARCHAR(100) NOT NULL DEFAULT '',
  unit_price NUMERIC(12,2) NOT NULL,
  quantity INTEGER NOT NULL,
  discount_per_item NUMERIC(12,2) NOT NULL DEFAULT 0
);
