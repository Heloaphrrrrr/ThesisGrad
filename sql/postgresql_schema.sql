CREATE TABLE customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    gender VARCHAR(16) NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    age_group VARCHAR(32) NOT NULL,
    customer_segment VARCHAR(32) NOT NULL
);

CREATE TABLE products (
    product_id BIGSERIAL PRIMARY KEY,
    category VARCHAR(64) NOT NULL UNIQUE,
    base_unit_price NUMERIC(12, 2),
    price_band VARCHAR(16)
);

CREATE TABLE shopping_malls (
    mall_id BIGSERIAL PRIMARY KEY,
    shopping_mall VARCHAR(128) NOT NULL UNIQUE,
    mall_tier VARCHAR(16),
    mall_popularity_score NUMERIC(8, 4)
);

CREATE TABLE transactions (
    invoice_no VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) NOT NULL REFERENCES customers(customer_id),
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    mall_id BIGINT NOT NULL REFERENCES shopping_malls(mall_id),
    quantity INTEGER NOT NULL CHECK (quantity >= 1),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    payment_method VARCHAR(32) NOT NULL,
    invoice_date DATE NOT NULL,
    unit_price NUMERIC(12, 2),
    invoice_year INTEGER NOT NULL,
    invoice_month INTEGER NOT NULL CHECK (invoice_month BETWEEN 1 AND 12),
    invoice_day INTEGER NOT NULL CHECK (invoice_day BETWEEN 1 AND 31),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_weekend BOOLEAN NOT NULL,
    quantity_band VARCHAR(16),
    price_deviation_from_category NUMERIC(12, 2)
);

CREATE INDEX idx_transactions_customer_id
    ON transactions (customer_id);

CREATE INDEX idx_transactions_product_id
    ON transactions (product_id);

CREATE INDEX idx_transactions_mall_id
    ON transactions (mall_id);

CREATE INDEX idx_transactions_invoice_date
    ON transactions (invoice_date);

CREATE INDEX idx_transactions_payment_method
    ON transactions (payment_method);

CREATE TABLE staging_customer_shopping_raw (
    row_number BIGSERIAL PRIMARY KEY,
    invoice_no TEXT,
    customer_id TEXT,
    gender TEXT,
    age TEXT,
    category TEXT,
    quantity TEXT,
    price TEXT,
    payment_method TEXT,
    invoice_date TEXT,
    shopping_mall TEXT,
    source_file VARCHAR(255),
    imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cleaning_runs (
    run_id BIGSERIAL PRIMARY KEY,
    run_mode VARCHAR(32) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    status VARCHAR(32) NOT NULL,
    notes TEXT
);

CREATE TABLE detected_issues (
    issue_id VARCHAR(64) PRIMARY KEY,
    run_id BIGINT REFERENCES cleaning_runs(run_id),
    row_id VARCHAR(32) NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    column_name VARCHAR(64) NOT NULL,
    issue_type VARCHAR(16) NOT NULL,
    current_value TEXT,
    suggested_value TEXT,
    confidence NUMERIC(6, 4),
    severity VARCHAR(16),
    severity_score NUMERIC(6, 4),
    reason TEXT,
    source_method VARCHAR(64),
    recommended_action VARCHAR(32),
    can_auto_fix BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_detected_issues_run_id
    ON detected_issues (run_id);

CREATE INDEX idx_detected_issues_row_id
    ON detected_issues (row_id);

CREATE TABLE fix_recommendations (
    recommendation_id BIGSERIAL PRIMARY KEY,
    issue_id VARCHAR(64) NOT NULL REFERENCES detected_issues(issue_id),
    row_id VARCHAR(32) NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    column_name VARCHAR(64) NOT NULL,
    suggested_value TEXT,
    confidence NUMERIC(6, 4),
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    applied_at TIMESTAMP
);

CREATE TABLE cleaning_actions (
    action_id BIGSERIAL PRIMARY KEY,
    issue_id VARCHAR(64) REFERENCES detected_issues(issue_id),
    invoice_no VARCHAR(32),
    table_name VARCHAR(64) NOT NULL,
    column_name VARCHAR(64) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    action_type VARCHAR(32) NOT NULL,
    action_status VARCHAR(32) NOT NULL,
    action_by VARCHAR(64) NOT NULL DEFAULT 'system',
    action_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dataset_profile (
    profile_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT REFERENCES cleaning_runs(run_id),
    table_name VARCHAR(64) NOT NULL,
    column_name VARCHAR(64) NOT NULL,
    missing_count INTEGER NOT NULL,
    missing_rate NUMERIC(8, 4) NOT NULL,
    unique_count INTEGER NOT NULL,
    min_value TEXT,
    max_value TEXT,
    issue_count INTEGER NOT NULL DEFAULT 0,
    anomaly_count INTEGER NOT NULL DEFAULT 0,
    invalid_count INTEGER NOT NULL DEFAULT 0,
    profiled_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE fixed_transactions (
    invoice_no VARCHAR(32) PRIMARY KEY REFERENCES transactions(invoice_no),
    customer_id VARCHAR(32) NOT NULL REFERENCES customers(customer_id),
    product_id BIGINT NOT NULL REFERENCES products(product_id),
    mall_id BIGINT NOT NULL REFERENCES shopping_malls(mall_id),
    quantity INTEGER NOT NULL CHECK (quantity >= 1),
    price NUMERIC(12, 2) NOT NULL CHECK (price >= 0),
    payment_method VARCHAR(32) NOT NULL,
    invoice_date DATE NOT NULL,
    unit_price NUMERIC(12, 2),
    invoice_year INTEGER NOT NULL,
    invoice_month INTEGER NOT NULL CHECK (invoice_month BETWEEN 1 AND 12),
    invoice_day INTEGER NOT NULL CHECK (invoice_day BETWEEN 1 AND 31),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_weekend BOOLEAN NOT NULL,
    quantity_band VARCHAR(16),
    price_deviation_from_category NUMERIC(12, 2),
    fixed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
