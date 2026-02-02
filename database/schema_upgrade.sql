-- Pro-uni schema upgrade (MySQL)
-- Run this if you're using an existing MySQL database.
-- Note: MySQL does not support "ADD COLUMN IF NOT EXISTS" on older versions.
-- If a statement fails because the column/index already exists, just skip it.

ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN totp_secret VARCHAR(64) NULL;
ALTER TABLE users ADD COLUMN vault_salt VARCHAR(64) NULL;

-- Indexes (optional)
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_mfa ON users(mfa_enabled);
