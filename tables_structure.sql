-- There are 4 table in the database

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `pword` varchar(255) NOT NULL,
  `clearance` int NOT NULL,
  `full_name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_name` varchar(255) NOT NULL,
  `ean13` varchar(15) NOT NULL,
  `price` float NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ean13` (`ean13`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions` (
  `transaction_id` varchar(16) NOT NULL,
  `total_amount` float DEFAULT NULL,
  `cashier_username` varchar(255) NOT NULL,
  `transaction_date` date DEFAULT NULL,
  PRIMARY KEY (`transaction_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transaction_items`
--

DROP TABLE IF EXISTS `transaction_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transaction_items` (
  `item_id` int NOT NULL AUTO_INCREMENT,
  `transaction_id` varchar(16) DEFAULT NULL,
  `item_name` varchar(255) DEFAULT NULL,
  `quantity` int DEFAULT NULL,
  `price_per_unit` float DEFAULT NULL,
  `ean13` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`item_id`),
  KEY `transaction_id` (`transaction_id`),
  CONSTRAINT `transaction_items_ibfk_1` FOREIGN KEY (`transaction_id`) REFERENCES `transactions` (`transaction_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;