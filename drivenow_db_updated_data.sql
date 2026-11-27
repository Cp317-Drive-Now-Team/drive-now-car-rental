-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: drivenow_db
-- ------------------------------------------------------
-- Server version	8.0.43

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
-- Table structure for table `cars`
--

DROP TABLE IF EXISTS `cars`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cars` (
  `car_id` int NOT NULL AUTO_INCREMENT,
  `make` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL,
  `year` int NOT NULL,
  `car_type` varchar(30) NOT NULL,
  `daily_rate` decimal(10,2) NOT NULL,
  `status` enum('Available','Rented','Maintenance') NOT NULL DEFAULT 'Available',
  `location_id` int NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`car_id`),
  KEY `location_id` (`location_id`),
  KEY `idx_car_search` (`make`,`model`,`year`,`car_type`,`status`),
  CONSTRAINT `cars_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`location_id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cars`
--

LOCK TABLES `cars` WRITE;
/*!40000 ALTER TABLE `cars` DISABLE KEYS */;
INSERT INTO `cars` VALUES (1,'Toyota','Corolla',2022,'Economy',45.00,'Available',1,1),(2,'Honda','Civic',2023,'Sedan',50.00,'Rented',1,1),(3,'Toyota','RAV4',2023,'SUV',70.00,'Available',1,1),(4,'Hyundai','Elantra',2022,'Sedan',55.00,'Available',1,1),(5,'Ford','Escape',2022,'SUV',75.00,'Rented',1,1),(6,'Subaru','Outback',2023,'SUV',80.00,'Available',1,1),(7,'Subaru','Outback',2023,'SUV',80.00,'Rented',1,1);
/*!40000 ALTER TABLE `cars` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `location_id` int NOT NULL AUTO_INCREMENT,
  `location_name` varchar(100) NOT NULL,
  `address` varchar(255) NOT NULL,
  `city` varchar(50) NOT NULL,
  `state_province` varchar(50) NOT NULL,
  `postal_code` varchar(20) NOT NULL,
  PRIMARY KEY (`location_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES (1,'University Campus Branch','75 University Ave W','Waterloo','Ontario','N2L 3C5');
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `payment_id` int NOT NULL AUTO_INCREMENT,
  `reservation_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_type` enum('Deposit','Full Payment','Refund') NOT NULL,
  `payment_method` varchar(50) NOT NULL,
  `transaction_token` varchar(255) NOT NULL,
  `payment_status` enum('Successful','Failed','Refunded') NOT NULL DEFAULT 'Successful',
  `payment_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`payment_id`),
  KEY `reservation_id` (`reservation_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`reservation_id`) REFERENCES `reservations` (`reservation_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
INSERT INTO `payments` VALUES (1,6,200.00,'Full Payment','Test Card','test_ok_c8b46305222567dc','Successful','2026-11-14 03:53:58'),(2,3,40.00,'Deposit','Test Card','test_ok_4c0b12781b3090a6','Successful','2026-11-14 03:54:57'),(3,3,160.00,'Full Payment','Test Card','test_decl_e60d753e8249d3a7','Failed','2026-11-14 03:56:16'),(4,3,40.00,'Refund','Test Card','test_refund_91451d8221a4fb92','Refunded','2026-11-14 03:57:01'),(5,7,30.00,'Deposit','Test Card','test_ok_647b6a136c83960c','Successful','2026-11-14 06:00:35'),(6,7,120.00,'Full Payment','Test Card','test_decl_4510d2a6aaff4e94','Failed','2026-11-14 06:01:08'),(7,7,120.00,'Full Payment','Test Card','test_ok_eaa22cc19633b36d','Successful','2026-11-14 06:01:25'),(8,6,200.00,'Refund','Test Card','test_refund_3b558310f2ba6b9c','Refunded','2026-11-14 06:02:23'),(9,8,64.00,'Deposit','Test Card','test_ok_21de8fe95d3848a8','Successful','2026-11-14 06:08:38'),(10,8,256.00,'Full Payment','Test Card','test_decl_5e42cf1093597b71','Failed','2026-11-14 06:09:14'),(11,8,256.00,'Full Payment','Test Card','test_ok_26e63e3a3a8514f9','Successful','2026-11-14 06:09:29'),(12,7,150.00,'Refund','Test Card','test_refund_7211b532432d6e7e','Refunded','2026-11-14 06:09:49');
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reservations`
--

DROP TABLE IF EXISTS `reservations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reservations` (
  `reservation_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `car_id` int NOT NULL,
  `pickup_location_id` int NOT NULL,
  `dropoff_location_id` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `total_cost` decimal(10,2) NOT NULL,
  `status` enum('Pending','Confirmed','Cancelled','Completed') NOT NULL DEFAULT 'Pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`reservation_id`),
  KEY `user_id` (`user_id`),
  KEY `pickup_location_id` (`pickup_location_id`),
  KEY `dropoff_location_id` (`dropoff_location_id`),
  KEY `idx_reservation_dates` (`car_id`,`start_date`,`end_date`,`status`),
  CONSTRAINT `reservations_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `reservations_ibfk_2` FOREIGN KEY (`car_id`) REFERENCES `cars` (`car_id`) ON DELETE RESTRICT,
  CONSTRAINT `reservations_ibfk_3` FOREIGN KEY (`pickup_location_id`) REFERENCES `locations` (`location_id`) ON DELETE RESTRICT,
  CONSTRAINT `reservations_ibfk_4` FOREIGN KEY (`dropoff_location_id`) REFERENCES `locations` (`location_id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reservations`
--

LOCK TABLES `reservations` WRITE;
/*!40000 ALTER TABLE `reservations` DISABLE KEYS */;
INSERT INTO `reservations` VALUES (1,2,1,1,1,'2026-11-15','2026-11-18',135.00,'Cancelled','2026-11-12 07:15:32'),(2,2,3,1,1,'2026-11-20','2026-11-25',350.00,'Cancelled','2026-11-12 07:15:32'),(3,2,2,1,1,'2026-12-01','2026-12-05',200.00,'Cancelled','2026-11-12 07:15:32'),(4,2,1,1,1,'2026-11-15','2026-11-18',135.00,'Cancelled','2026-11-12 07:15:37'),(5,2,3,1,1,'2026-11-20','2026-11-25',350.00,'Cancelled','2026-11-12 07:15:37'),(6,2,2,1,1,'2026-12-01','2026-12-05',200.00,'Cancelled','2026-11-12 07:15:37'),(7,2,5,1,1,'2026-12-13','2026-12-15',150.00,'Cancelled','2026-11-14 05:59:56'),(8,2,7,1,1,'2026-12-22','2026-12-26',320.00,'Confirmed','2026-11-14 06:08:08');
/*!40000 ALTER TABLE `reservations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `phone_number` varchar(20) DEFAULT NULL,
  `driver_license_number` varchar(50) DEFAULT NULL,
  `role` enum('Customer','Administrator') NOT NULL DEFAULT 'Customer',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `driver_license_number` (`driver_license_number`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Admin','Staff','admin@drivenow.com','scrypt:32768:8:1$enLVo9XpKuteMOl8$9bea0b1d80f3ef1c42ce6c8f841f7f82c4a0b7fe45a7453db10b10fb5fb89e907698d37bfbfd2b5e1963cc6a6e57ec3111301c38961d29c9a982fc1940146591',NULL,NULL,'Administrator','2026-10-23 16:53:29'),(2,'Alex','Morgan','alex.morgan@example.com','scrypt:32768:8:1$enLVo9XpKuteMOl8$9bea0b1d80f3ef1c42ce6c8f841f7f82c4a0b7fe45a7453db10b10fb5fb89e907698d37bfbfd2b5e1963cc6a6e57ec3111301c38961d29c9a982fc1940146591',NULL,'DL-987654321','Customer','2026-10-23 16:53:29'),(3,'Admin','Manager','admin.staff@drivenow.com','scrypt:32768:8:1$enLVo9XpKuteMOl8$9bea0b1d80f3ef1c42ce6c8f841f7f82c4a0b7fe45a7453db10b10fb5fb89e907698d37bfbfd2b5e1963cc6a6e57ec3111301c38961d29c9a982fc1940146591','519-555-0100',NULL,'Administrator','2026-10-26 20:50:57'),(4,'Jane','Doe','jane.doe@example.com','scrypt:32768:8:1$enLVo9XpKuteMOl8$9bea0b1d80f3ef1c42ce6c8f841f7f82c4a0b7fe45a7453db10b10fb5fb89e907698d37bfbfd2b5e1963cc6a6e57ec3111301c38961d29c9a982fc1940146591','519-555-0199','DL-123456789-ON','Customer','2026-10-26 20:50:57'),(5,'Aryan','Kainth','kain0140@mylaurier.ca','scrypt:32768:8:1$enLVo9XpKuteMOl8$9bea0b1d80f3ef1c42ce6c8f841f7f82c4a0b7fe45a7453db10b10fb5fb89e907698d37bfbfd2b5e1963cc6a6e57ec3111301c38961d29c9a982fc1940146591',NULL,'NL-213456789-DL','Customer','2026-10-29 22:39:07');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-13 20:28:59
