-- Migration 012: Website login credentials and durable payment authorities

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20),
  ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
  ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_number
  ON users(phone_number)
  WHERE phone_number IS NOT NULL;

ALTER TABLE transactions
  ADD COLUMN IF NOT EXISTS authority VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_authority
  ON transactions(authority)
  WHERE authority IS NOT NULL;
