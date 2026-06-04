CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL DEFAULT 'user',
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Поля 2FA
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    two_factor_code VARCHAR(6) DEFAULT NULL,
    two_factor_expired_at TIMESTAMPTZ DEFAULT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

INSERT INTO users (username, email, password_hash, role, is_blocked, is_verified, created_at)
VALUES
    ('admin', 'admin@example.com', crypt('adminadmin1', gen_salt('bf', 12)), 'admin', FALSE, TRUE, NOW()),
    ('auditor', 'auditor@example.com', crypt('auditor111', gen_salt('bf', 12)), 'auditor', FALSE, TRUE, NOW())
ON CONFLICT (email) DO UPDATE
SET
    username = EXCLUDED.username,
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_blocked = EXCLUDED.is_blocked,
    is_verified = EXCLUDED.is_verified;
