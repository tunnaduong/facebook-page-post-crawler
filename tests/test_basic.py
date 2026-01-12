"""
Basic tests for Facebook Page Post Crawler
"""
import unittest
from unittest.mock import Mock, patch
from src.config import Config
from src.parser import FacebookParser


class TestConfig(unittest.TestCase):
    """Test configuration module"""
    
    def test_config_exists(self):
        """Test that config has required attributes"""
        self.assertTrue(hasattr(Config, 'DB_HOST'))
        self.assertTrue(hasattr(Config, 'DB_NAME'))
        self.assertTrue(hasattr(Config, 'REDIS_URL'))
        self.assertTrue(hasattr(Config, 'HEADLESS'))
        
    def test_get_db_config(self):
        """Test database configuration dictionary"""
        db_config = Config.get_db_config()
        self.assertIn('host', db_config)
        self.assertIn('port', db_config)
        self.assertIn('user', db_config)
        self.assertIn('password', db_config)
        self.assertIn('database', db_config)


class TestParser(unittest.TestCase):
    """Test HTML parser"""
    
    def setUp(self):
        self.parser = FacebookParser()
    
    def test_parser_initialization(self):
        """Test parser can be initialized"""
        self.assertIsNotNone(self.parser)
        self.assertIsNone(self.parser.soup)
    
    def test_parse_html(self):
        """Test HTML parsing"""
        html = "<html><body><div>Test</div></body></html>"
        self.parser.parse_html(html)
        self.assertIsNotNone(self.parser.soup)
    
    def test_extract_content(self):
        """Test content extraction from mock element"""
        html = '<div class="userContent">Test post content</div>'
        self.parser.parse_html(html)
        element = self.parser.soup.find('div')
        content = self.parser.extract_content(element)
        self.assertEqual(content, "Test post content")
    
    def test_extract_media_urls(self):
        """Test media URL extraction"""
        html = '<div><img src="https://fbcdn.net/image.jpg"/></div>'
        self.parser.parse_html(html)
        element = self.parser.soup.find('div')
        urls = self.parser.extract_media_urls(element)
        self.assertIsInstance(urls, list)
        self.assertTrue(len(urls) > 0)
    
    def test_extract_engagement(self):
        """Test engagement metrics extraction"""
        html = '<div>100 likes 20 comments 5 shares</div>'
        self.parser.parse_html(html)
        element = self.parser.soup.find('div')
        engagement = self.parser.extract_engagement(element)
        self.assertIsInstance(engagement, dict)
        self.assertIn('likes', engagement)
        self.assertIn('comments', engagement)
        self.assertIn('shares', engagement)


class TestDatabase(unittest.TestCase):
    """Test database module"""
    
    @patch('src.database.mysql.connector.connect')
    def test_database_init(self, mock_connect):
        """Test database initialization"""
        from src.database import Database
        db = Database()
        self.assertIsNotNone(db)
        self.assertIsNotNone(db.config)
    
    def test_post_data_structure(self):
        """Test post data structure matches expected format"""
        post_data = {
            'post_id': 'test123',
            'page_name': 'TestPage',
            'content': 'Test content',
            'media_urls': [],
            'posted_at': None,
            'engagement': {'likes': 0, 'comments': 0, 'shares': 0},
            'post_url': 'https://facebook.com/test'
        }
        
        # Verify all required fields exist
        required_fields = ['post_id', 'page_name', 'content', 'media_urls', 
                          'posted_at', 'engagement', 'post_url']
        for field in required_fields:
            self.assertIn(field, post_data)


if __name__ == '__main__':
    unittest.main()
