-- Initial PostgreSQL setup for AI Writer PRO
-- This script runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create additional schemas if needed
-- CREATE SCHEMA IF NOT EXISTS analytics;
-- CREATE SCHEMA IF NOT EXISTS logs;

-- Set timezone
SET timezone = 'UTC';

-- Create initial database user with proper permissions
-- (The main user is already created by environment variables)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE ai_writer_db TO ai_writer_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO ai_writer_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_writer_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_writer_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ai_writer_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ai_writer_user;

-- Create initial tables (these will be managed by Alembic migrations)
-- But we can create some utility functions here

-- Function to generate UUID v4
CREATE OR REPLACE FUNCTION generate_uuid_v4()
RETURNS UUID AS $$
BEGIN
    RETURN uuid_generate_v4();
END;
$$ LANGUAGE plpgsql;

-- Function to get current timestamp in UTC
CREATE OR REPLACE FUNCTION get_utc_timestamp()
RETURNS TIMESTAMP WITH TIME ZONE AS $$
BEGIN
    RETURN NOW() AT TIME ZONE 'UTC';
END;
$$ LANGUAGE plpgsql;

-- Log the initialization
DO $$
BEGIN
    RAISE NOTICE 'AI Writer PRO database initialized successfully';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user;
    RAISE NOTICE 'Timezone: %', current_setting('timezone');
END $$;
