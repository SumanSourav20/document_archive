-- init.sql
DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'document_archive'
    ) THEN
        CREATE DATABASE document_archive;
    END IF;
END
$$;
