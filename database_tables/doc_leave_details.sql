-- Table schema for `doc_leave_details`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `doc_leave_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) DEFAULT NULL,
  `rank` varchar(50) DEFAULT NULL,
  `name` varchar(150) DEFAULT NULL,
  `company` varchar(100) DEFAULT NULL,
  `leave_type` varchar(50) DEFAULT NULL,
  `leave_days` int DEFAULT NULL,
  `from_date` date DEFAULT NULL,
  `to_date` date DEFAULT NULL,
  `onco_status` varchar(50) DEFAULT '',
  `doc_status` varchar(50) DEFAULT '',
  `action_status` varchar(100) DEFAULT '',
  `created_by` varchar(150) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `published_by` varchar(100) DEFAULT NULL,
  `published_role` varchar(100) DEFAULT NULL,
  `published_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_army_number` (`army_number`),
  KEY `idx_onco_status` (`onco_status`),
  KEY `idx_doc_status` (`doc_status`),
  KEY `idx_published_at` (`published_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
