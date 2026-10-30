-- Table schema for `leave_status_info`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `leave_status_info` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `name` varchar(45) NOT NULL,
  `leave_type` varchar(50) NOT NULL,
  `leave_days` int NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `request_sent_to` varchar(150) DEFAULT NULL,
  `request_status` varchar(50) DEFAULT 'Pending',
  `recommend_date` datetime DEFAULT NULL,
  `rejected_date` datetime DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `leave_reason` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `reject_reason` text,
  `company` varchar(50) DEFAULT NULL,
  `prefix_date` date DEFAULT NULL,
  `suffix_date` date DEFAULT NULL,
  `prefix_days` int DEFAULT '0',
  `suffix_days` int DEFAULT '0',
  `rank` varchar(45) DEFAULT NULL,
  `reliever_army_number` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_leave_status_updated` (`request_status`,`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
