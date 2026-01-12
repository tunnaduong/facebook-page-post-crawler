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
                elif '/videos/' in href:
                    match = re.search(r'/videos/(\d+)', href)
                    if match:
                        return 'video_' + match.group(1)
            
            # Method 2: Check data attributes
            if post_element.get('data-ft'):
                data_ft = post_element.get('data-ft')
                match = re.search(r'"mf_story_key":"(\d+)"', data_ft)
                if match:
                    return match.group(1)
            
            # Method 3: Check for aria-label or other identifying attributes
            aria_label = post_element.get('aria-label')
            if aria_label:
                # Try to extract timestamp or unique identifier from aria-label
                match = re.search(r'(\d{10,})', aria_label)
                if match:
                    return match.group(1)
            
            # Method 4: Use element ID if available
            element_id = post_element.get('id')
            if element_id and (element_id.startswith('post') or element_id.startswith('hyperfeed')):
                return element_id
            
            # Method 5: Generate ID from content hash (last resort)
            content = self.extract_content(post_element)
            timestamp = self.extract_timestamp(post_element)
            if content or timestamp:
                import hashlib
                # Create a deterministic ID from content and timestamp
                id_string = f"{content[:100]}_{timestamp}"
                hash_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                logger.debug(f"Generated fallback post ID: {hash_id}")
                return f"generated_{hash_id}"
                
        except Exception as e:
            logger.error(f"Error extracting post ID: {e}")
            
        return None
    
    def extract_content(self, post_element) -> str:
        """Extract post text content"""
        try:
            # Look for common Facebook post content selectors
            # These may vary based on Facebook's HTML structure
            content_selectors = [
                # Modern selectors
                {'data-ad-preview': 'message'},
                {'data-ad-comet-preview': 'message'},
                # Common selectors
                {'data-testid': 'post_message'},
                {'class': 'userContent'},
                {'class': '_5pbx userContent'},
                # Look for specific div patterns
                {'class': lambda x: x and 'userContent' in str(x)},
            ]
            
            for selector in content_selectors:
                content_elem = post_element.find('div', selector)
                if content_elem:
                    text = content_elem.get_text(strip=True)
                    if text and len(text) > 0:
                        return text
            
            # Try to find span or p tags with substantial text
            for tag in ['span', 'p', 'div']:
                elements = post_element.find_all(tag)
                for elem in elements:
                    # Skip if it's likely a button or navigation element
                    if elem.get('role') in ['button', 'link', 'navigation']:
                        continue
                    text = elem.get_text(strip=True)
                    # Only consider if it has substantial content
                    if text and len(text) > 20:
                        return text
            
            # Fallback: get all text from the post element
            full_text = post_element.get_text(strip=True)
            if full_text and len(full_text) > 0:
                return full_text[:500]  # Limit length to avoid junk
            
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
                logger.debug("Could not extract post ID, skipping post")
                return None
            
            # Extract all available data
            content = self.extract_content(post_element)
            media_urls = self.extract_media_urls(post_element)
            posted_at = self.extract_timestamp(post_element)
            engagement = self.extract_engagement(post_element)
            post_url = self.extract_post_url(post_element)
            
            # Only return post if we have at least some content or media
            if not content and not media_urls:
                logger.debug(f"Post {post_id} has no content or media, skipping")
                return None
            
            post_data = {
                'post_id': post_id,
                'page_name': page_name,
                'content': content,
                'media_urls': media_urls,
                'posted_at': posted_at,
                'engagement': engagement,
                'post_url': post_url
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
        
        # Check if we're hitting a login wall
        if self._check_login_required():
            logger.warning("Facebook is requiring login to view this page. Posts may not be visible.")
            logger.warning("Try logging in first or use cookies from an authenticated session.")
        
        # Find all post elements
        # Facebook structure varies, try multiple selectors in order of specificity
        post_selectors = [
            # Modern Facebook selectors (2024+)
            {'role': 'article'},
            {'data-pagelet': lambda x: x and 'FeedUnit' in x},
            {'class': lambda x: x and any(cls in str(x) for cls in ['x1yztbdb', 'x1n2onr6'])},
            # Older selectors as fallback
            {'data-testid': 'fbfeed_story'},
            {'class': '_5pcr userContentWrapper'},
            {'class': lambda x: x and 'userContentWrapper' in str(x)},
        ]
        
        post_elements = []
        for i, selector in enumerate(post_selectors):
            try:
                elements = self.soup.find_all('div', selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector #{i+1}: {selector}")
                    post_elements.extend(elements)
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # If no elements found with specific selectors, try broader search
        if not post_elements:
            logger.warning("No elements found with specific selectors, trying broader search...")
            # Look for divs with role=article anywhere
            post_elements = self.soup.find_all('div', {'role': 'article'})
            if not post_elements:
                # Last resort: find divs that contain links to /posts/ or /permalink/
                all_divs = self.soup.find_all('div')
                for div in all_divs:
                    links = div.find_all('a', href=True, recursive=False)
                    for link in links:
                        if any(pattern in link['href'] for pattern in ['/posts/', '/permalink/', 'story_fbid=']):
                            post_elements.append(div)
                            break
        
        logger.info(f"Found {len(post_elements)} potential post elements")
        
        # Deduplicate elements (sometimes nested structures cause duplicates)
        seen_ids = set()
        unique_elements = []
        for elem in post_elements:
            elem_id = id(elem)
            if elem_id not in seen_ids:
                seen_ids.add(elem_id)
                unique_elements.append(elem)
        
        logger.info(f"Processing {len(unique_elements)} unique post elements")
        
        for post_elem in unique_elements:
            post_data = self.parse_post(post_elem, page_name)
            if post_data:
                posts.append(post_data)
        
        logger.info(f"Successfully parsed {len(posts)} posts")
        return posts
    
    def _check_login_required(self) -> bool:
        """Check if Facebook is requiring login"""
        if not self.soup:
            return False
        
        # Check for common login-related elements
        login_indicators = [
            self.soup.find('form', {'id': 'login_form'}),
            self.soup.find('input', {'name': 'email'}),
            self.soup.find('input', {'name': 'pass'}),
            self.soup.find(string=lambda text: text and 'log in' in text.lower()),
        ]
        
        return any(login_indicators)
