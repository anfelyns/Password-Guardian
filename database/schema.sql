-- schema.sql - ORM-Compatible Database Schema for Password Guardian
-- This schema matches the SQLAlchemy models exactly

CREATE DATABASE IF NOT EXISTS `password_guardian`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `password_guardian`;

-- ============================================================
-- Users Table
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `salt` VARCHAR(255) NOT NULL,
  `email_verified` TINYINT(1) DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `last_login` TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_email` (`email`),
  INDEX `idx_username` (`username`),
  INDEX `idx_email_verified` (`email_verified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Passwords Table
-- ============================================================
CREATE TABLE IF NOT EXISTS `passwords` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `site_name` VARCHAR(100) NOT NULL,
  `site_icon` VARCHAR(10) DEFAULT '🔒',
  `username` VARCHAR(255) NOT NULL,
  `encrypted_password` TEXT NOT NULL,
  `category` ENUM('personal','work','finance','study','game','trash') DEFAULT 'personal',
  `strength` ENUM('weak','medium','strong') DEFAULT 'medium',
  `favorite` TINYINT(1) DEFAULT 0,
  `trashed_at` TIMESTAMP NULL DEFAULT NULL,
  `last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_category` (`category`),
  INDEX `idx_favorite` (`favorite`),
  INDEX `idx_strength` (`strength`),
  INDEX `idx_trashed_at` (`trashed_at`),
  CONSTRAINT `fk_passwords_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Password History Table (Audit Trail)
-- ============================================================
CREATE TABLE IF NOT EXISTS `password_history` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `password_id` INT NOT NULL,
  `old_encrypted_password` TEXT NOT NULL,
  `changed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_password_id` (`password_id`),
  CONSTRAINT `fk_history_password`
    FOREIGN KEY (`password_id`) REFERENCES `passwords` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- OTP/2FA Codes Table
-- ============================================================
CREATE TABLE IF NOT EXISTS `otp_codes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `code` VARCHAR(6) NOT NULL,
  `purpose` VARCHAR(50) DEFAULT 'login',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  `verified` TINYINT(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_purpose` (`purpose`),
  INDEX `idx_verified` (`verified`),
  INDEX `idx_expires_at` (`expires_at`),
  CONSTRAINT `fk_otp_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Sessions Table
-- ============================================================
CREATE TABLE IF NOT EXISTS `sessions` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `session_token` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `expires_at` TIMESTAMP NOT NULL,
  `device_info` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_session_token` (`session_token`),
  INDEX `idx_expires_at` (`expires_at`),
  CONSTRAINT `fk_session_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- User Devices Table
-- ============================================================
CREATE TABLE IF NOT EXISTS `user_devices` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `device_name` VARCHAR(255) NOT NULL,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `last_used` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_last_used` (`last_used`),
  CONSTRAINT `fk_device_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Activity Logs Table
-- ============================================================
CREATE TABLE IF NOT EXISTS `activity_logs` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `action` VARCHAR(100) NOT NULL,
  `details` TEXT,
  `ip_address` VARCHAR(45) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_action` (`action`),
  INDEX `idx_created_at` (`created_at`),
  CONSTRAINT `fk_log_user`
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Optional: Sample Data for Testing
-- ============================================================
-- Uncomment to insert test data

/*
-- Test User (password: "TestPassword123")
INSERT INTO `users` (`username`, `email`, `password_hash`, `salt`, `email_verified`, `created_at`) 
VALUES (
  'test_user',
  'test@example.com',
  '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92',  -- hashed password
  'test_salt_12345',
  1,
  NOW()
);

-- Sample Password Entry
INSERT INTO `passwords` (`user_id`, `site_name`, `site_icon`, `username`, `encrypted_password`, `category`, `strength`, `favorite`)
VALUES (
  1,  -- user_id (first user)
  'GitHub',
  '🐙',
  'test_user',
  'gcm1:encrypted_blob_here',  -- This should be actual encrypted data
  'work',
  'strong',
  1
);
*/

-- ============================================================
-- Verification Queries
-- ============================================================
-- Run these to verify your schema:

-- Check all tables
-- SHOW TABLES;

-- Check users table structure
-- DESCRIBE users;

-- Check passwords table structure
-- DESCRIBE passwords;

-- Check foreign key relationships
-- SELECT 
--   TABLE_NAME,
--   COLUMN_NAME,
--   CONSTRAINT_NAME,
--   REFERENCED_TABLE_NAME,
--   REFERENCED_COLUMN_NAME
-- FROM information_schema.KEY_COLUMN_USAGE
-- WHERE TABLE_SCHEMA = 'password_guardian'
--   AND REFERENCED_TABLE_NAME IS NOT NULL;

-- ============================================================
-- Cleanup Commands (USE WITH CAUTION!)
-- ============================================================
-- Uncomment ONLY if you want to DROP ALL TABLES and start fresh

/*
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `activity_logs`;
DROP TABLE IF EXISTS `user_devices`;
DROP TABLE IF EXISTS `sessions`;
DROP TABLE IF EXISTS `otp_codes`;
DROP TABLE IF EXISTS `password_history`;
DROP TABLE IF EXISTS `passwords`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;
*/
