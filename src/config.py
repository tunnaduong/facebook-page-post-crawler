"""
Configuration management for Facebook Page Post Crawler
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'facebook_crawler')
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Crawler Configuration
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    CRAWL_INTERVAL = int(os.getenv('CRAWL_INTERVAL', 3600))  # seconds
    RANDOM_DELAY_MIN = int(os.getenv('RANDOM_DELAY_MIN', 2))
    RANDOM_DELAY_MAX = int(os.getenv('RANDOM_DELAY_MAX', 5))
    
    # Facebook Configuration
    FB_EMAIL = os.getenv('FB_EMAIL', '')
    FB_PASSWORD = os.getenv('FB_PASSWORD', '')
    
    # Proxy Configuration (Optional)
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_URL = os.getenv('PROXY_URL', '')
    
    # Paths
    COOKIES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cookies')
    
    @classmethod
    def get_db_config(cls):
        """Get database configuration as dictionary"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
        }
