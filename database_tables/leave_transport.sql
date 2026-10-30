-- Table schema for `leave_transport`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `leave_transport` (
  `transport_id` int NOT NULL AUTO_INCREMENT,
  `leave_request_id` int NOT NULL,
  `onward_mode` enum('Air','Train','') DEFAULT '',
  `onward_air_type` enum('Charter','Civil','') DEFAULT '',
  `onward_train_type` enum('CV Warrant','Free','') DEFAULT '',
  `return_mode` enum('Air','Train','') DEFAULT '',
  `return_air_type` enum('Charter','Civil','') DEFAULT '',
  `return_train_type` enum('CV Warrant','Free','') DEFAULT '',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`transport_id`),
  KEY `leave_transport_ibfk_1` (`leave_request_id`),
  CONSTRAINT `leave_transport_ibfk_1` FOREIGN KEY (`leave_request_id`) REFERENCES `leave_status_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
