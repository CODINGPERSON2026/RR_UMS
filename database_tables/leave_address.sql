-- Table schema for `leave_address`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `leave_address` (
  `address_id` int NOT NULL AUTO_INCREMENT,
  `leave_request_id` int NOT NULL,
  `same_as_permanent` tinyint(1) DEFAULT '1',
  `address_line1` varchar(255) DEFAULT NULL,
  `address_line2` varchar(255) DEFAULT NULL,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `pincode` varchar(20) DEFAULT NULL,
  `mobile` varchar(20) DEFAULT NULL,
  `alternate_contact` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`address_id`),
  KEY `leave_address_ibfk_1` (`leave_request_id`),
  CONSTRAINT `leave_address_ibfk_1` FOREIGN KEY (`leave_request_id`) REFERENCES `leave_status_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
