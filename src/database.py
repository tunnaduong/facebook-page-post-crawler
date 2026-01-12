"""
Database operations for Facebook Page Post Crawler
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import mysql.connector
from mysql.connector import Error
from src.config import Config

logger = logging.getLogger(__name__)


class Database:
    """Database handler for MySQL operations"""
    
    def __init__(self):
        self.config = Config.get_db_config()
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info("Successfully connected to MySQL database")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return False
            
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
            
    def execute_query(self, query: str, params: tuple = None):
        """Execute a query without returning results"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"Error executing query: {e}")
            self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
                
    def fetch_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error fetching query: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
    
    def post_exists(self, post_id: str) -> bool:
        """Check if a post already exists in database"""
        query = "SELECT id FROM fb_posts WHERE post_id = %s"
        result = self.fetch_query(query, (post_id,))
        return len(result) > 0
    
    def insert_post(self, post_data: Dict[str, Any]) -> int:
        """Insert a new post into database"""
        query = """
        INSERT INTO fb_posts 
        (post_id, page_name, content, media_urls, posted_at, engagement, post_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        params = (
            post_data['post_id'],
            post_data['page_name'],
            post_data.get('content', ''),
            json.dumps(post_data.get('media_urls', [])),
            post_data.get('posted_at'),
            json.dumps(post_data.get('engagement', {})),
            post_data.get('post_url', '')
        )
        
        return self.execute_query(query, params)
    
    def update_post(self, post_id: str, post_data: Dict[str, Any]):
        """Update an existing post"""
        query = """
        UPDATE fb_posts 
        SET content = %s, media_urls = %s, engagement = %s, updated_at = CURRENT_TIMESTAMP
        WHERE post_id = %s
        """
        
        params = (
            post_data.get('content', ''),
            json.dumps(post_data.get('media_urls', [])),
            json.dumps(post_data.get('engagement', {})),
            post_id
        )
        
        return self.execute_query(query, params)
    
    def save_post(self, post_data: Dict[str, Any]) -> tuple:
        """
        Save a post to database (insert if new, update if exists)
        Returns: (success: bool, is_new: bool)
        """
        try:
            post_id = post_data['post_id']
            
            if self.post_exists(post_id):
                self.update_post(post_id, post_data)
                logger.info(f"Updated existing post: {post_id}")
                return (True, False)
            else:
                self.insert_post(post_data)
                logger.info(f"Inserted new post: {post_id}")
                return (True, True)
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return (False, False)
    
    def create_crawl_log(self, page_name: str) -> int:
        """Create a new crawl log entry"""
        query = """
        INSERT INTO crawl_logs (page_name, status)
        VALUES (%s, 'running')
        """
        return self.execute_query(query, (page_name,))
    
    def update_crawl_log(self, log_id: int, status: str, posts_found: int = 0, 
                        posts_new: int = 0, posts_updated: int = 0, 
                        error_message: str = None):
        """Update crawl log with results"""
        query = """
        UPDATE crawl_logs
        SET status = %s, finished_at = CURRENT_TIMESTAMP,
            posts_found = %s, posts_new = %s, posts_updated = %s, error_message = %s
        WHERE id = %s
        """
        params = (status, posts_found, posts_new, posts_updated, error_message, log_id)
        return self.execute_query(query, params)
    
    def get_recent_posts(self, page_name: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get recent posts, optionally filtered by page name"""
        if page_name:
            query = """
            SELECT * FROM fb_posts 
            WHERE page_name = %s 
            ORDER BY posted_at DESC 
            LIMIT %s
            """
            params = (page_name, limit)
        else:
            query = """
            SELECT * FROM fb_posts 
            ORDER BY posted_at DESC 
            LIMIT %s
            """
            params = (limit,)
            
        return self.fetch_query(query, params)
    
    def get_active_pages(self) -> List[Dict]:
        """Get list of active pages to monitor"""
        query = "SELECT * FROM fb_pages WHERE is_active = TRUE"
        return self.fetch_query(query)
