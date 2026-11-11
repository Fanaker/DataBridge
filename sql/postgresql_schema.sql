-- PostgreSQL companion schema for DataBridge (local SQLite demo runs without Docker).
CREATE SCHEMA IF NOT EXISTS databridge;
CREATE TABLE IF NOT EXISTS databridge.products (
 sku TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
 cost NUMERIC(12,2) NOT NULL, price NUMERIC(12,2) NOT NULL
);
CREATE TABLE IF NOT EXISTS databridge.orders (
 order_id TEXT PRIMARY KEY, order_date TIMESTAMP NOT NULL,
 sku TEXT NOT NULL REFERENCES databridge.products(sku),
 quantity INTEGER NOT NULL CHECK (quantity>0), unit_price NUMERIC(12,2) NOT NULL CHECK(unit_price>0),
 channel TEXT NOT NULL, customer_id TEXT NOT NULL, source TEXT NOT NULL,
 created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS db_orders_date_idx ON databridge.orders(order_date);
CREATE INDEX IF NOT EXISTS db_orders_source_idx ON databridge.orders(source);
CREATE TABLE IF NOT EXISTS databridge.runs (
 id BIGSERIAL PRIMARY KEY, started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),source TEXT NOT NULL,
 read_count INT NOT NULL,accepted INT NOT NULL,duplicates INT NOT NULL,rejected INT NOT NULL,
 duration_ms INT NOT NULL,status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS databridge.rejects (
 id BIGSERIAL PRIMARY KEY,run_id BIGINT REFERENCES databridge.runs(id),row_number INT,order_id TEXT,
 reason TEXT NOT NULL,raw_json JSONB NOT NULL
);
