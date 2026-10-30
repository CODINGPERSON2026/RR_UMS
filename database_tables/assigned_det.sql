-- Table schema for `assigned_det`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `assigned_det` (
  `army_number` varchar(15) NOT NULL,
  `det_id` int DEFAULT NULL,
  `assigned_on` datetime DEFAULT CURRENT_TIMESTAMP,
  `det_removed_date` datetime DEFAULT NULL,
  `det_status` tinyint(1) DEFAULT '1',
  KEY `idx_assigned_det_status` (`det_status`,`army_number`),
  KEY `idx_assigned_det_id` (`det_id`),
  KEY `idx_assigned_det_status_army` (`det_status`,`army_number`,`det_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
