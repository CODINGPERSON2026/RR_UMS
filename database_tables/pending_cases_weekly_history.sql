-- Table schema for `pending_cases_weekly_history`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `pending_cases_weekly_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_id` int DEFAULT NULL,
  `type_of_case` varchar(100) NOT NULL,
  `week_identifier` varchar(30) NOT NULL,
  `week_start_date` date NOT NULL,
  `week_end_date` date NOT NULL,
  `pending_last_week` int DEFAULT '0',
  `recd_current_week` int DEFAULT '0',
  `total_cases` int DEFAULT '0',
  `pub_this_week` int DEFAULT '0',
  `under_prog` int DEFAULT '0',
  `remarks` text,
  `rollover_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_case_week` (`type_of_case`,`week_identifier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

