"""
Facebook Page Crawler using Playwright
"""
import os
import json
import time
import random
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from playwright.sync_api import sync_playwright, Page, Browser
from playwright_stealth import stealth_sync

from src.config import Config
from src.parser import FacebookParser
from src.database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FacebookCrawler:
    """Crawler for Facebook pages using Playwright"""
    
    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else Config.HEADLESS
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.parser = FacebookParser()
        self.db = Database()
        self.cookies_path = Path(Config.COOKIES_DIR)
        self.cookies_path.mkdir(exist_ok=True)
        
    def _random_delay(self, min_sec: int = None, max_sec: int = None):
        """Add a random delay to simulate human behavior"""
        min_sec = min_sec or Config.RANDOM_DELAY_MIN
        max_sec = max_sec or Config.RANDOM_DELAY_MAX
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"Sleeping for {delay:.2f} seconds")
        time.sleep(delay)
    
    def _get_cookie_file(self, identifier: str = 'default') -> Path:
        """Get path to cookie file"""
        return self.cookies_path / f'cookies_{identifier}.json'
    
    def save_cookies(self, identifier: str = 'default'):
        """Save browser cookies to file"""
        if not self.page:
            logger.warning("No page available to save cookies")
            return
            
        cookies = self.page.context.cookies()
        cookie_file = self._get_cookie_file(identifier)
        
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f, indent=2)
        
        logger.info(f"Saved cookies to {cookie_file}")
    
    def load_cookies(self, identifier: str = 'default') -> bool:
        """Load cookies from file"""
        cookie_file = self._get_cookie_file(identifier)
        
        if not cookie_file.exists():
            logger.info(f"No cookie file found at {cookie_file}")
            return False
        
        try:
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            self.page.context.add_cookies(cookies)
            logger.info(f"Loaded cookies from {cookie_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            return False
    
    def start_browser(self):
        """Initialize Playwright browser"""
        logger.info("Starting browser...")
        
        playwright = sync_playwright().start()
        
        # Browser launch options
        launch_options = {
            'headless': self.headless,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        }
        
        # Add proxy if configured
        if Config.USE_PROXY and Config.PROXY_URL:
            launch_options['proxy'] = {'server': Config.PROXY_URL}
        
        self.browser = playwright.chromium.launch(**launch_options)
        
        # Create context with realistic settings
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = context.new_page()
        
        # Apply stealth mode
        stealth_sync(self.page)
        
        logger.info("Browser started successfully")
    
    def stop_browser(self):
        """Close browser"""
        if self.browser:
            self.browser.close()
            logger.info("Browser closed")
    
    def login(self, email: str = None, password: str = None) -> bool:
        """
        Login to Facebook (manual or automated)
        
        Note: This is a basic implementation. For production,
        consider manual login with cookie saving.
        """
        email = email or Config.FB_EMAIL
        password = password or Config.FB_PASSWORD
        
        if not email or not password:
            logger.warning("No credentials provided. Please login manually.")
            return False
        
        try:
            logger.info("Attempting to login to Facebook...")
            self.page.goto('https://www.facebook.com/login')
            self._random_delay(2, 4)
            
            # Fill login form
            self.page.fill('input[name="email"]', email)
            self._random_delay(1, 2)
            self.page.fill('input[name="pass"]', password)
            self._random_delay(1, 2)
            
            # Click login button
            self.page.click('button[name="login"]')
            self._random_delay(5, 8)
            
            # Check if login was successful
            if 'login' not in self.page.url.lower():
                logger.info("Login successful")
                self.save_cookies()
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            return False
    
    def scroll_page(self, scrolls: int = 5):
        """
        Scroll page to load more content
        
        Args:
            scrolls: Number of times to scroll down
        """
        logger.info(f"Scrolling page {scrolls} times to load content...")
        
        for i in range(scrolls):
            # Scroll to bottom
            self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            self._random_delay(2, 4)
            
            # Scroll up a bit (natural behavior)
            if i % 3 == 0:
                self.page.evaluate('window.scrollBy(0, -300)')
                self._random_delay(1, 2)
        
        logger.info("Scrolling completed")
    
    def crawl_page(self, page_url: str, page_name: str = None, scrolls: int = 5) -> List[Dict[str, Any]]:
        """
        Crawl a Facebook page and extract posts
        
        Args:
            page_url: URL of the Facebook page
            page_name: Name identifier for the page
            scrolls: Number of times to scroll to load more posts
            
        Returns:
            List of parsed posts
        """
        if not page_name:
            # Extract page name from URL
            page_name = page_url.split('/')[-1] or page_url.split('/')[-2]
        
        logger.info(f"Crawling page: {page_name} ({page_url})")
        
        try:
            # Navigate to page
            self.page.goto(page_url, wait_until='networkidle', timeout=60000)
            self._random_delay(3, 5)
            
            # Scroll to load more posts
            self.scroll_page(scrolls)
            
            # Get page HTML
            html_content = self.page.content()
            
            # Parse posts
            posts = self.parser.find_posts(html_content, page_name)
            
            logger.info(f"Successfully crawled {len(posts)} posts from {page_name}")
            return posts
            
        except Exception as e:
            logger.error(f"Error crawling page {page_name}: {e}")
            return []
    
    def save_posts_to_db(self, posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Save posts to database
        
        Returns:
            Dictionary with counts of new and updated posts
        """
        stats = {'new': 0, 'updated': 0, 'failed': 0}
        
        if not self.db.connection or not self.db.connection.is_connected():
            self.db.connect()
        
        for post in posts:
            success, is_new = self.db.save_post(post)
            if success:
                if is_new:
                    stats['new'] += 1
                else:
                    stats['updated'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"Saved posts - New: {stats['new']}, Updated: {stats['updated']}, Failed: {stats['failed']}")
        return stats
    
    def run(self, page_url: str, page_name: str = None, scrolls: int = 5, 
            use_cookies: bool = True, save_to_db: bool = True) -> Dict[str, Any]:
        """
        Main crawl execution
        
        Args:
            page_url: URL of Facebook page to crawl
            page_name: Name identifier for the page
            scrolls: Number of scroll iterations
            use_cookies: Whether to load saved cookies
            save_to_db: Whether to save results to database
            
        Returns:
            Dictionary with crawl results
        """
        results = {
            'success': False,
            'posts_found': 0,
            'posts_new': 0,
            'posts_updated': 0,
            'error': None
        }
        
        log_id = None
        
        try:
            # Start browser
            self.start_browser()
            
            # Load cookies or login
            if use_cookies:
                self.load_cookies()
            
            # Navigate to Facebook first to check if logged in
            self.page.goto('https://www.facebook.com', timeout=60000)
            self._random_delay(2, 4)
            
            # Check if we need to login
            if 'login' in self.page.url.lower():
                logger.warning("Not logged in. Attempting login...")
                self.login()
            
            # Connect to database if saving
            if save_to_db:
                self.db.connect()
                if not page_name:
                    page_name = page_url.split('/')[-1] or page_url.split('/')[-2]
                log_id = self.db.create_crawl_log(page_name)
            
            # Crawl the page
            posts = self.crawl_page(page_url, page_name, scrolls)
            results['posts_found'] = len(posts)
            
            # Print posts to console (Phase 2 requirement)
            logger.info("\n" + "="*80)
            logger.info(f"CRAWLED POSTS FROM {page_name}")
            logger.info("="*80)
            for i, post in enumerate(posts, 1):
                logger.info(f"\nPost {i}:")
                logger.info(f"  ID: {post['post_id']}")
                logger.info(f"  Content: {post['content'][:100]}...")
                logger.info(f"  Media: {len(post['media_urls'])} items")
                logger.info(f"  Engagement: {post['engagement']}")
                logger.info(f"  URL: {post['post_url']}")
            logger.info("="*80 + "\n")
            
            # Save to database
            if save_to_db and posts:
                stats = self.save_posts_to_db(posts)
                results['posts_new'] = stats['new']
                results['posts_updated'] = stats['updated']
            
            results['success'] = True
            
            # Update crawl log
            if save_to_db and log_id:
                self.db.update_crawl_log(
                    log_id, 'completed',
                    posts_found=results['posts_found'],
                    posts_new=results['posts_new'],
                    posts_updated=results['posts_updated']
                )
            
        except Exception as e:
            logger.error(f"Error during crawl execution: {e}")
            results['error'] = str(e)
            
            # Update crawl log with error
            if save_to_db and log_id:
                self.db.update_crawl_log(log_id, 'failed', error_message=str(e))
        
        finally:
            # Cleanup
            self.stop_browser()
            if save_to_db:
                self.db.disconnect()
        
        return results


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Facebook Page Post Crawler')
    parser.add_argument('--page', required=True, help='Facebook page URL or username')
    parser.add_argument('--name', help='Page name identifier')
    parser.add_argument('--scrolls', type=int, default=5, help='Number of scroll iterations')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-cookies', action='store_true', help='Do not use saved cookies')
    parser.add_argument('--no-save', action='store_true', help='Do not save to database')
    
    args = parser.parse_args()
    
    # Convert page name to URL if needed
    page_url = args.page
    if not page_url.startswith('http'):
        page_url = f'https://www.facebook.com/{page_url}'
    
    # Run crawler
    crawler = FacebookCrawler(headless=args.headless)
    results = crawler.run(
        page_url=page_url,
        page_name=args.name,
        scrolls=args.scrolls,
        use_cookies=not args.no_cookies,
        save_to_db=not args.no_save
    )
    
    # Print results
    print("\n" + "="*80)
    print("CRAWL RESULTS")
    print("="*80)
    print(f"Success: {results['success']}")
    print(f"Posts found: {results['posts_found']}")
    print(f"Posts new: {results['posts_new']}")
    print(f"Posts updated: {results['posts_updated']}")
    if results['error']:
        print(f"Error: {results['error']}")
    print("="*80)


if __name__ == '__main__':
    main()
