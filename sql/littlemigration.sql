DROP TABLE IF EXISTS cleaning_actions;
DROP TABLE IF EXISTS fix_recommendations;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS dataset_profile;
DROP TABLE IF EXISTS detected_issues;

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
