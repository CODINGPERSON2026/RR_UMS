-- Table schema for `grant_allocations`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `grant_allocations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `grant_id` int NOT NULL,
  `amount` decimal(12,2) NOT NULL,
  `allocation_type` enum('Original','Additional') DEFAULT 'Additional',
  `remarks` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `financial_year` varchar(9) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `grant_id` (`grant_id`),
  CONSTRAINT `grant_allocations_ibfk_1` FOREIGN KEY (`grant_id`) REFERENCES `grants` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
