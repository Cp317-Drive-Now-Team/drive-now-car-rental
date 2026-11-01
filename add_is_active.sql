-- Run once in MySQL Workbench (needed for CAR-01.3 "removed cars")
USE drivenow_db;
ALTER TABLE cars ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1;
