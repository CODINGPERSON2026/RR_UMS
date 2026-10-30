-- Table schema for `project_bill_of_materials`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `project_bill_of_materials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `project_id` int DEFAULT NULL,
  `project_title` varchar(255) NOT NULL,
  `project_head` varchar(255) NOT NULL,
  `nomenclature` varchar(255) NOT NULL,
  `au` varchar(50) DEFAULT NULL,
  `qty` int DEFAULT '0',
  `rate` decimal(12,2) DEFAULT '0.00',
  `total_cost` decimal(12,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `project_id` (`project_id`),
  CONSTRAINT `project_bill_of_materials_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
