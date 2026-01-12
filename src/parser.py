"""
HTML Parser for Facebook posts using BeautifulSoup
"""
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class FacebookParser:
    """Parser for Facebook page posts"""
    
    def __init__(self):
        self.soup = None
        
    def parse_html(self, html_content: str):
        """Parse HTML content with BeautifulSoup"""
        self.soup = BeautifulSoup(html_content, 'lxml')
        
    def extract_post_id(self, post_element) -> Optional[str]:
        """Extract post ID from post element"""
        try:
            # Try to find post ID in various attributes
            # Facebook post IDs are usually in data-ft or href attributes
            
            # Method 1: Check for permalink/story_fbid in links
            links = post_element.find_all('a', href=True)
            for link in links:
                href = link['href']
                # Pattern: /permalink/ or /story.php?story_fbid=
                if '/permalink/' in href:
                    match = re.search(r'/permalink/(\d+)', href)
                    if match:
                        return match.group(1)
                elif 'story_fbid=' in href:
                    match = re.search(r'story_fbid=(\d+)', href)
                    if match:
                        return match.group(1)
                elif '/posts/' in href:
                    match = re.search(r'/posts/(\d+)', href)
                    if match:
                        return match.group(1)
            
            # Method 2: Check data attributes
            if post_element.get('data-ft'):
                data_ft = post_element.get('data-ft')
                match = re.search(r'"mf_story_key":"(\d+)"', data_ft)
                if match:
                    return match.group(1)
            
            # Method 3: Use element ID if available
            element_id = post_element.get('id')
            if element_id and element_id.startswith('post'):
                return element_id
                
        except Exception as e:
            logger.error(f"Error extracting post ID: {e}")
            
        return None
    
    def extract_content(self, post_element) -> str:
        """Extract post text content"""
        try:
            # Look for common Facebook post content selectors
            # These may vary based on Facebook's HTML structure
            content_selectors = [
                {'data-testid': 'post_message'},
                {'class': 'userContent'},
                {'class': '_5pbx userContent'},
            ]
            
            for selector in content_selectors:
                content_elem = post_element.find('div', selector)
                if content_elem:
                    return content_elem.get_text(strip=True)
            
            # Fallback: get all text
            return post_element.get_text(strip=True)[:500]  # Limit length
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return ""
    
    def extract_media_urls(self, post_element) -> List[str]:
        """Extract image and video URLs from post"""
        media_urls = []
        
        try:
            # Extract images
            images = post_element.find_all('img')
            for img in images:
                src = img.get('src')
                if src and ('fbcdn' in src or 'facebook' in src):
                    # Filter out profile pictures and small icons
                    if 'emoji' not in src and 'safe_image' not in src:
                        media_urls.append(src)
            
            # Extract videos
            videos = post_element.find_all('video')
            for video in videos:
                src = video.get('src')
                if src:
                    media_urls.append(src)
                    
        except Exception as e:
            logger.error(f"Error extracting media URLs: {e}")
            
        return media_urls
    
    def extract_timestamp(self, post_element) -> Optional[datetime]:
        """Extract post timestamp"""
        try:
            # Look for timestamp elements
            time_elements = post_element.find_all(['abbr', 'time'])
            
            for elem in time_elements:
                # Check for data-utime attribute (Unix timestamp)
                if elem.get('data-utime'):
                    timestamp = int(elem.get('data-utime'))
                    return datetime.fromtimestamp(timestamp)
                
                # Check for datetime attribute
                if elem.get('datetime'):
                    return datetime.fromisoformat(elem.get('datetime').replace('Z', '+00:00'))
                    
        except Exception as e:
            logger.error(f"Error extracting timestamp: {e}")
            
        return None
    
    def extract_engagement(self, post_element) -> Dict[str, int]:
        """Extract engagement metrics (likes, comments, shares)"""
        engagement = {
            'likes': 0,
            'comments': 0,
            'shares': 0
        }
        
        try:
            # Look for engagement text
            text = post_element.get_text()
            
            # Extract likes
            like_match = re.search(r'([\d,]+)\s*(?:likes?|thích)', text, re.IGNORECASE)
            if like_match:
                try:
                    engagement['likes'] = int(like_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            # Extract comments
            comment_match = re.search(r'([\d,]+)\s*(?:comments?|bình luận)', text, re.IGNORECASE)
            if comment_match:
                try:
                    engagement['comments'] = int(comment_match.group(1).replace(',', ''))
                except ValueError:
                    pass
            
            # Extract shares
            share_match = re.search(r'([\d,]+)\s*(?:shares?|chia sẻ)', text, re.IGNORECASE)
            if share_match:
                try:
                    engagement['shares'] = int(share_match.group(1).replace(',', ''))
                except ValueError:
                    pass
                
        except Exception as e:
            logger.error(f"Error extracting engagement: {e}")
            
        return engagement
    
    def extract_post_url(self, post_element) -> str:
        """Extract direct URL to the post"""
        try:
            links = post_element.find_all('a', href=True)
            for link in links:
                href = link['href']
                if any(pattern in href for pattern in ['/permalink/', '/posts/', 'story_fbid=']):
                    # Make sure it's a full URL
                    if not href.startswith('http'):
                        href = 'https://www.facebook.com' + href
                    return href.split('?')[0]  # Remove query parameters
        except Exception as e:
            logger.error(f"Error extracting post URL: {e}")
            
        return ""
    
    def parse_post(self, post_element, page_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single post element and extract all data
        
        Returns:
            Dictionary with post data or None if parsing failed
        """
        try:
            post_id = self.extract_post_id(post_element)
            
            if not post_id:
                logger.warning("Could not extract post ID, skipping post")
                return None
            
            post_data = {
                'post_id': post_id,
                'page_name': page_name,
                'content': self.extract_content(post_element),
                'media_urls': self.extract_media_urls(post_element),
                'posted_at': self.extract_timestamp(post_element),
                'engagement': self.extract_engagement(post_element),
                'post_url': self.extract_post_url(post_element)
            }
            
            logger.debug(f"Parsed post: {post_id}")
            return post_data
            
        except Exception as e:
            logger.error(f"Error parsing post: {e}")
            return None
    
    def find_posts(self, html_content: str, page_name: str) -> List[Dict[str, Any]]:
        """
        Find and parse all posts in HTML content
        
        Args:
            html_content: HTML string from Facebook page
            page_name: Name of the Facebook page
            
        Returns:
            List of parsed post dictionaries
        """
        self.parse_html(html_content)
        posts = []
        
        # Find all post elements
        # Facebook structure varies, try multiple selectors
        post_selectors = [
            {'role': 'article'},
            {'data-testid': 'fbfeed_story'},
            {'class': '_5pcr userContentWrapper'},
        ]
        
        post_elements = []
        for selector in post_selectors:
            elements = self.soup.find_all('div', selector)
            if elements:
                post_elements.extend(elements)
                break
        
        logger.info(f"Found {len(post_elements)} potential post elements")
        
        for post_elem in post_elements:
            post_data = self.parse_post(post_elem, page_name)
            if post_data:
                posts.append(post_data)
        
        logger.info(f"Successfully parsed {len(posts)} posts")
        return posts
