-- init_db.sql

-- Create script_logs table if it doesn't already exist
CREATE TABLE IF NOT EXISTS script_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    output TEXT,
    error TEXT
);
