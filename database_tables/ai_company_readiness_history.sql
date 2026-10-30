-- Table schema for `ai_company_readiness_history`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `ai_company_readiness_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `snapshot_date` date NOT NULL,
  `strength_score` float NOT NULL,
  `qualification_score` float NOT NULL,
  `course_score` float NOT NULL,
  `trade_score` float NOT NULL,
  `fitness_score` float NOT NULL,
  `medical_score` float NOT NULL,
  `availability_score` float NOT NULL,
  `overall_readiness` float NOT NULL,
  `main_gap_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gap_count` int DEFAULT '0',
  `actual_strength` int DEFAULT '0',
  `required_strength` int DEFAULT '0',
  `available_strength` int DEFAULT '0',
  `unfit_count` int DEFAULT '0',
  `onleave_count` int DEFAULT '0',
  `detachment_count` int DEFAULT '0',
  `td_count` int DEFAULT '0',
  `oncourse_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_comp_date` (`company`,`snapshot_date`),
  KEY `idx_company_hist` (`company`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
