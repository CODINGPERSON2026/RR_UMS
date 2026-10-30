-- Table schema for `pending_cases_company_recd`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `pending_cases_company_recd` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_id` int NOT NULL,
  `company` varchar(100) NOT NULL,
  `recd_count` int NOT NULL DEFAULT '0',
  `updated_by` varchar(100) DEFAULT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_case_company` (`case_id`,`company`),
  KEY `idx_company` (`company`),
  CONSTRAINT `fk_pccr_case` FOREIGN KEY (`case_id`) REFERENCES `pending_cases` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

