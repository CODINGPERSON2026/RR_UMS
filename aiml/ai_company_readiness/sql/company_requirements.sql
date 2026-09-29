-- ==========================================================
-- UMS AI Company Readiness Database Baseline Schema
-- ==========================================================

-- 1. Baseline Requirements Table
-- Stores authorized operational requirements for each company
CREATE TABLE IF NOT EXISTS ai_company_requirements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company VARCHAR(100) NOT NULL,
    requirement_type VARCHAR(100) NOT NULL,
    requirement_name VARCHAR(255) NOT NULL,
    required_count INT NOT NULL DEFAULT 0,
    priority VARCHAR(50) DEFAULT 'Medium',
    status VARCHAR(20) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_company (company),
    INDEX idx_requirement_type (requirement_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Periodic Readiness History Table
-- Stores periodic snapshots of calculated readiness for auditing and ML training
CREATE TABLE IF NOT EXISTS ai_company_readiness_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company VARCHAR(100) NOT NULL,
    snapshot_date DATE NOT NULL,
    strength_score FLOAT NOT NULL,
    qualification_score FLOAT NOT NULL,
    course_score FLOAT NOT NULL,
    trade_score FLOAT NOT NULL,
    fitness_score FLOAT NOT NULL,
    medical_score FLOAT NOT NULL,
    availability_score FLOAT NOT NULL,
    overall_readiness FLOAT NOT NULL,
    main_gap_type VARCHAR(100),
    gap_count INT DEFAULT 0,
    actual_strength INT DEFAULT 0,
    required_strength INT DEFAULT 0,
    available_strength INT DEFAULT 0,
    unfit_count INT DEFAULT 0,
    onleave_count INT DEFAULT 0,
    detachment_count INT DEFAULT 0,
    td_count INT DEFAULT 0,
    oncourse_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_comp_date (company, snapshot_date),
    INDEX idx_company_hist (company)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
