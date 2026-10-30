-- Table schema for `company_interview`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `company_interview` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(45) NOT NULL,
  `interview_status` tinyint NOT NULL DEFAULT '0',
  `interview_done_on` date DEFAULT NULL,
  `remarks` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `co_interview_status` tinyint NOT NULL DEFAULT '0',
  `co_interview_done_on` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
