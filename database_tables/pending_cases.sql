-- Table schema for `pending_cases`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `pending_cases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type_of_case` varchar(100) NOT NULL,
  `pending_last_week` int DEFAULT '0',
  `recd_current_week` int DEFAULT '0',
  `pub_this_week` int DEFAULT '0',
  `total_cases` int DEFAULT '0',
  `under_prog` int DEFAULT '0',
  `remarks` text,
  `updated_by` varchar(100) DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `sort_order` int DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
