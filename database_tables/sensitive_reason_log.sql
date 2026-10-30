-- Table schema for `sensitive_reason_log`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `sensitive_reason_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `reason` text NOT NULL,
  `added_by` varchar(100) NOT NULL,
  `added_by_role` varchar(50) DEFAULT NULL,
  `added_on` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `idx_sensitive_log_army_date` (`army_number`,`added_on`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
