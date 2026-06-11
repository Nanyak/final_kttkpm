-- Payment Service schema (PostgreSQL)
CREATE TABLE payments (
  id BIGSERIAL PRIMARY KEY,
  payment_code VARCHAR(50) NOT NULL UNIQUE,
  order_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  amount NUMERIC(14,2) NOT NULL,
  currency VARCHAR(10) NOT NULL DEFAULT 'VND',
  method VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  transaction_id VARCHAR(255) NULL,
  gateway_response JSONB NOT NULL DEFAULT '{}',
  failure_reason TEXT NULL,
  paid_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);

CREATE TABLE payment_refunds (
  id BIGSERIAL PRIMARY KEY,
  payment_id BIGINT NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
  refund_amount NUMERIC(14,2) NOT NULL,
  reason TEXT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  refund_transaction_id VARCHAR(255) NULL,
  created_at TIMESTAMPTZ NOT NULL,
  processed_at TIMESTAMPTZ NULL
);
