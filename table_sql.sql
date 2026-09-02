-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: localhost    Database: hrms
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `monthly_medical_status`
--

DROP TABLE IF EXISTS `monthly_medical_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `monthly_medical_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `year` int NOT NULL,
  `month` tinyint NOT NULL,
  `unit` varchar(50) NOT NULL,
  `unfit_count` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_year_month_unit` (`year`,`month`,`unit`)
) ENGINE=InnoDB AUTO_INCREMENT=2845 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `monthly_medical_status`
--

LOCK TABLES `monthly_medical_status` WRITE;
/*!40000 ALTER TABLE `monthly_medical_status` DISABLE KEYS */;
INSERT INTO `monthly_medical_status` VALUES (43,2026,3,'All',217,'2026-03-10 18:28:57'),(47,2026,3,'3 Company',83,'2026-03-10 18:29:01'),(48,2026,3,'HQ company',91,'2026-03-10 18:29:03'),(2809,2026,5,'All',196,'2026-05-06 08:26:06'),(2812,2026,5,'3 Company',39,'2026-05-06 08:26:06'),(2813,2026,5,'HQ company',83,'2026-05-06 08:26:06'),(2814,2026,6,'All',202,'2026-06-01 01:34:11'),(2817,2026,6,'3 Company',36,'2026-06-01 01:34:11'),(2818,2026,6,'HQ company',84,'2026-06-01 01:34:11'),(2838,2026,3,'COMN company',83,'2026-09-02 08:36:55'),(2839,2026,5,'COMN company',74,'2026-09-02 08:36:55'),(2840,2026,6,'COMN company',82,'2026-09-02 08:36:55'),(2841,2026,9,'All',149,'2026-09-02 08:38:43'),(2842,2026,9,'COMN Company',60,'2026-09-02 08:38:43'),(2843,2026,9,'3 Company',24,'2026-09-02 08:38:44'),(2844,2026,9,'HQ company',65,'2026-09-02 08:38:44');
/*!40000 ALTER TABLE `monthly_medical_status` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-02 15:33:05
