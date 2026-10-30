-- Table schema for `leave_journey_legs`
-- Auto-created if not exists at runtime

CREATE TABLE IF NOT EXISTS `leave_journey_legs` (
  `leg_id` int NOT NULL AUTO_INCREMENT,
  `transport_id` int NOT NULL,
  `journey_type` enum('onward','return') NOT NULL,
  `leg_order` int NOT NULL,
  `from_station` varchar(100) NOT NULL,
  `to_station` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`leg_id`),
  KEY `leave_journey_legs_ibfk_1` (`transport_id`),
  CONSTRAINT `leave_journey_legs_ibfk_1` FOREIGN KEY (`transport_id`) REFERENCES `leave_transport` (`transport_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
