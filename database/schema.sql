-- Facebook Page Post Crawler Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS facebook_crawler
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE facebook_crawler;

-- Table to store Facebook posts
CREATE TABLE IF NOT EXISTS fb_posts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(100) UNIQUE NOT NULL COMMENT 'Unique Facebook post ID',
    page_name VARCHAR(255) NOT NULL COMMENT 'Name of the Facebook page',
    content TEXT COMMENT 'Post text content',
    media_urls JSON COMMENT 'Array of image/video URLs',
    posted_at TIMESTAMP NULL COMMENT 'When the post was published on Facebook',
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When the post was crawled',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update time',
    engagement JSON COMMENT 'Engagement metrics: likes, comments, shares',
    post_url VARCHAR(500) COMMENT 'Full URL to the post',
    INDEX idx_post_id (post_id),
    INDEX idx_page_name (page_name),
    INDEX idx_posted_at (posted_at),
    INDEX idx_crawled_at (crawled_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to store crawl sessions/logs
CREATE TABLE IF NOT EXISTS crawl_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    page_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP NULL,
    posts_found INT DEFAULT 0,
    posts_new INT DEFAULT 0,
    posts_updated INT DEFAULT 0,
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    error_message TEXT,
    INDEX idx_page_name (page_name),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to store Facebook pages being monitored
CREATE TABLE IF NOT EXISTS fb_pages (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    page_name VARCHAR(255) UNIQUE NOT NULL,
    page_url VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_crawled_at TIMESTAMP NULL,
    crawl_frequency_minutes INT DEFAULT 60 COMMENT 'How often to crawl (in minutes)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_page_name (page_name),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
