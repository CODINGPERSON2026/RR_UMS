-- Table schema for `pending_case_remarks`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `pending_case_remarks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_id` int NOT NULL,
  `remark` text NOT NULL,
  `remarked_by` varchar(150) DEFAULT NULL,
  `remarked_by_role` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_case_id` (`case_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
