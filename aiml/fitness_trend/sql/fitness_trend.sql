-- ====================================================================
-- UMS - AI/ML Individual Fitness Trend & Prediction Tables
-- Isolated tables for predictions history, logs, and retraining metadata
-- ====================================================================

CREATE TABLE IF NOT EXISTS `ai_fitness_prediction_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `army_number` VARCHAR(50) NOT NULL,
    `personnel_name` VARCHAR(150),
    `rank_name` VARCHAR(100),
    `company` VARCHAR(100),
    `fitness_score` DECIMAL(5,2) NOT NULL,
    `fitness_category` VARCHAR(50) NOT NULL,
    `confidence_score` DECIMAL(5,2) NOT NULL,
    `bmi` DECIMAL(5,2),
    `weight_deviation_kg` DECIMAL(5,2),
    `model_version` VARCHAR(50) NOT NULL,
    `prediction_factors_json` TEXT,
    `recommendations_summary` TEXT,
    `generated_by` VARCHAR(100),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_fitness_army_no` (`army_number`),
    INDEX `idx_fitness_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `ai_fitness_model_audit` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `model_version` VARCHAR(50) NOT NULL,
    `algorithm_classifier` VARCHAR(100),
    `algorithm_regressor` VARCHAR(100),
    `training_records_count` INT,
    `accuracy` DECIMAL(5,4),
    `f1_score` DECIMAL(5,4),
    `mae` DECIMAL(5,4),
    `r2_score` DECIMAL(5,4),
    `metrics_json` TEXT,
    `trained_by` VARCHAR(100),
    `trained_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
