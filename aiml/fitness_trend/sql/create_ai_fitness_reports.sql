-- ====================================================================
-- UMS - AI/ML Individual Fitness Reports Table
-- Persists generated AI fitness reports, predictions, recommendations,
-- and progression data for role-based executive oversight.
-- ====================================================================

CREATE TABLE IF NOT EXISTS `ai_fitness_reports` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,

    `personnel_id` INT NULL,
    `army_number` VARCHAR(50) NOT NULL,
    `name` VARCHAR(150),
    `rank` VARCHAR(100),
    `company` VARCHAR(100),

    `age` INT NULL,
    `height_cm` DECIMAL(6,2) NULL,
    `actual_weight_kg` DECIMAL(6,2) NULL,
    `ideal_weight_kg` DECIMAL(6,2) NULL,
    `bmi` DECIMAL(6,2) NULL,

    `fitness_score` DECIMAL(6,2) NULL,
    `fitness_status` VARCHAR(100) NULL,

    `prediction_result` LONGTEXT NULL,

    `recommendations` LONGTEXT NULL,
    `diet_recommendations` LONGTEXT NULL,
    `exercise_recommendations` LONGTEXT NULL,

    `progression_prediction` LONGTEXT NULL,

    `report_language` VARCHAR(50) DEFAULT 'English',

    `report_generated` BOOLEAN DEFAULT TRUE,

    `pdf_path` VARCHAR(500) NULL,

    `model_name` VARCHAR(150) NULL,
    `model_version` VARCHAR(100) NULL,

    `generated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX `idx_army_number` (`army_number`),
    INDEX `idx_personnel_id` (`personnel_id`),
    INDEX `idx_company` (`company`),
    INDEX `idx_fitness_status` (`fitness_status`),
    INDEX `idx_generated_at` (`generated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
