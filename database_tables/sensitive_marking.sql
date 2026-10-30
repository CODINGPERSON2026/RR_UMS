-- Table schema for `sensitive_marking`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `sensitive_marking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `army_number` varchar(100) DEFAULT NULL,
  `reason` text,
  `marked_on` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_sensitive_marking_army` (`army_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
