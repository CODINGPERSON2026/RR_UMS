-- Table schema for `jco_kunda_assignment`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `jco_kunda_assignment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(50) NOT NULL,
  `additional_assigned_home_state` varchar(100) NOT NULL,
  `interview_status` enum('Pending','Done') DEFAULT 'Pending',
  `assigned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
