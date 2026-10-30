-- Table schema for `leave_details`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `leave_details` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(100) NOT NULL,
  `year` varchar(10) NOT NULL,
  `AL` int DEFAULT '0',
  `CL` int DEFAULT '0',
  `AAL` int DEFAULT '0',
  `PL` int DEFAULT '0',
  `remarks` text,
  `leave_start_date` date DEFAULT NULL,
  `leave_end_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `personnel_id` int DEFAULT NULL,
  `sr_no` int DEFAULT NULL,
  `Annual Leave` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
