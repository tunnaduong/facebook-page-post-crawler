"""
HTML Parser for Facebook posts using BeautifulSoup
"""

import re
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Constants for post ID extraction
ELEMENT_ID_PREFIXES = ["post", "hyperfeed"]


class FacebookParser:
    """Parser for Facebook page posts"""

    def __init__(self):
        self.soup = None

    def parse_html(self, html_content: str):
        """Parse HTML content with BeautifulSoup"""
        self.soup = BeautifulSoup(html_content, "lxml")

    def extract_post_id(self, post_element) -> Optional[str]:
        """Extract post ID from post element"""
        try:
            # Method 1: Check for permalink/story_fbid in links (Most reliable)
            links = post_element.find_all("a", href=True)
            for link in links:
                href = link["href"]

                # Try to get story_fbid from query params
                if "story_fbid=" in href:
                    match = re.search(r"story_fbid=([^&]+)", href)
                    if match:
                        return match.group(1)

                # Pattern: /permalink/ID
                if "/permalink/" in href:
                    match = re.search(r"/permalink/([^/]+)", href)
                    if match:
                        return match.group(1).split("?")[0]

                # Pattern: /posts/ID
                elif "/posts/" in href:
                    match = re.search(r"/posts/([^/]+)", href)
                    if match:
                        return match.group(1).split("?")[0]

                # Pattern: /videos/ID
                elif "/videos/" in href:
                    match = re.search(r"/videos/([^/]+)", href)
                    if match:
                        return match.group(1).split("?")[0]

            # Method 2: Check data attributes
            if post_element.get("data-ft"):
                data_ft = post_element.get("data-ft")
                match = re.search(r'"mf_story_key":"(\d+)"', data_ft)
                if match:
                    return match.group(1)

            # Method 3: Check for aria-label or other identifying attributes
            aria_label = post_element.get("aria-label")
            if aria_label:
                # Try to extract timestamp or unique identifier from aria-label
                match = re.search(r"(\d{10,})", aria_label)
                if match:
                    return match.group(1)

            # Method 4: Use element ID if available
            element_id = post_element.get("id")
            if element_id and any(
                element_id.startswith(prefix) for prefix in ELEMENT_ID_PREFIXES
            ):
                return element_id

            # Method 5: Generate ID from content hash (last resort)
            content = self.extract_content(post_element)
            timestamp = self.extract_timestamp(post_element)
            if content or timestamp:
                # Create a deterministic ID from content and timestamp
                id_string = f"{content[:100]}_{timestamp}"
                hash_id = hashlib.md5(id_string.encode()).hexdigest()[:16]
                logger.debug(f"Generated fallback post ID: {hash_id}")
                return f"generated_{hash_id}"

        except Exception as e:
            logger.error(f"Error extracting post ID: {e}")

        return None

    def extract_content(self, post_element) -> str:
        """
        Extract post text content using structural selectors.
        Focuses on Comet (Modern) Facebook classes and attributes.
        """
        try:
            # 1. Target the main content container by attribute
            # This is the most reliable way in modern Facebook Comet UI
            content_container = post_element.find(
                "div", {"data-ad-comet-preview": "message"}
            )
            if not content_container:
                content_container = post_element.find(
                    "div", {"data-ad-preview": "message"}
                )

            if content_container:
                # FB Comet nested spans with dir="auto" carry the text parts.
                # separator=" " ensures we don't merge words from different spans.
                text = content_container.get_text(separator=" ", strip=True)
                if text:
                    return text

            # 2. Structural Fallback: Look for specific content-bearing classes
            # x11i5rnm, xat24cr, x1mh8g0r are frequently used for post body text
            potential_text_parts = []
            for elem in post_element.find_all(["div", "span"], {"dir": "auto"}):
                # Skip if it's a child of a button or link (UI elements)
                if elem.find_parent(["button", "a"]):
                    continue

                # These classes are very common for the actual post text in the DOM
                cls_list = elem.get("class", [])
                cls_str = (
                    " ".join(cls_list) if isinstance(cls_list, list) else str(cls_list)
                )
                if any(
                    c in cls_str for c in ["x11i5rnm", "x1mh8g0r", "xt0b8zv", "xat24cr"]
                ):
                    text = elem.get_text(strip=True)
                    if text and text not in potential_text_parts and len(text) > 3:
                        potential_text_parts.append(text)

            if potential_text_parts:
                return " ".join(potential_text_parts)

            # 3. Fallback: Standard userContent class (Old Layouts)
            old_content = post_element.find("div", class_="userContent")
            if old_content:
                return old_content.get_text(separator=" ", strip=True)

            # 4. Global Fallback: Get all text that isn't in a UI element
            all_text = []
            # Find all elements with text that aren't buttons or links
            for elem in post_element.find_all(string=True):
                txt = elem.strip()
                if len(txt) > 20:  # Slightly shorter threshold
                    parent = elem.find_parent(["button", "a", "script", "style"])
                    if not parent:
                        # Basic junk check
                        if not any(
                            trash in txt.lower()
                            for trash in ["nhắn tin", "theo dõi", "chia sẻ"]
                        ):
                            # Ensure it's not just a date or simple counter
                            if not re.match(
                                r"^(\d+[hmdy]|Just now|Vừa xong|[\d.,]+ (likes?|thích|shares?|chia sẻ|comments?|bình luận))$",
                                txt,
                                re.I,
                            ):
                                all_text.append(txt)

            if all_text:
                # Deduplicate and join
                unique_txt = []
                for t in all_text:
                    if t not in unique_txt:
                        unique_txt.append(t)

                content = " ".join(unique_txt)
                # Strip trailing "Xem thêm" or "See more" which might be leftover from buttons
                content = re.sub(
                    r"\s*…\s*(Xem thêm|See more)\s*$", "", content, flags=re.I
                )
                content = re.sub(r"\s*(Xem thêm|See more)\s*$", "", content, flags=re.I)
                return content.strip()

        except Exception as e:
            logger.error(f"Error extracting content: {e}")

        return ""

    def _is_valid_media(self, src: str, element) -> bool:
        """Helper to validate if a media URL is an actual content image"""
        if not src or not isinstance(src, str):
            return False

        # 1. Filter out known UI sizes/patterns
        junk_patterns = [
            "/cp0/",
            "emoji",
            "safe_image",
            "s64x64",
            "s80x80",
            "s160x160",
            "p50x50",
            "p160x160",
        ]
        if any(p in src for p in junk_patterns):
            return False

        # 2. Skip if it's in a comment/avatar section
        parent_info = str(element.find_parent(class_=True))
        if any(x in parent_info for x in ["comment", "reply", "avatar"]):
            return False

        # 3. Check for tiny dimensions if available
        width = element.get("width")
        height = element.get("height")
        try:
            if width and int(str(width).replace("px", "")) < 100:
                return False
            if height and int(str(height).replace("px", "")) < 100:
                return False
        except ValueError:
            pass

        return True

    def extract_media_urls(self, post_element) -> List[str]:
        """Extract image and video URLs from post"""
        media_urls = []

        try:
            # 1. Standard images and SVGs
            images = post_element.find_all(["img", "image"])
            for img in images:
                # Check multiple attributes for the image source
                for attr in [
                    "src",
                    "xlink:href",
                    "data-src",
                    "data-full-size-image-url",
                    "data-img-src",
                ]:
                    src = img.get(attr)
                    if src and self._is_valid_media(src, img):
                        media_urls.append(src)

            # 2. Check for background-image in styles (common for grid layouts)
            for div in post_element.find_all("div", style=True):
                style = div.get("style", "")
                if "background-image" in style:
                    match = re.search(r'url\((["\']?)(.*?)\1\)', style)
                    if match:
                        url = match.group(2)
                        if self._is_valid_media(url, div):
                            media_urls.append(url)

            # 3. Check for specific Facebook data attributes for images
            for elem in post_element.find_all(attrs={"data-ploi": True}):
                url = elem.get("data-ploi")
                if url and self._is_valid_media(url, elem):
                    media_urls.append(url)

            # Extract videos
            videos = post_element.find_all("video")
            for video in videos:
                src = video.get("src")
                if src:
                    media_urls.append(src)
                else:
                    poster = video.get("poster")
                    if poster:
                        media_urls.append(poster)

        except Exception as e:
            logger.error(f"Error extracting media URLs: {e}")

        # Deduplicate while preserving order
        seen = set()
        return [x for x in media_urls if not (x in seen or seen.add(x))]

    def extract_timestamp(self, post_element) -> Optional[datetime]:
        """Extract post timestamp"""
        try:
            # Look for timestamp elements
            time_elements = post_element.find_all(["abbr", "time"])

            for elem in time_elements:
                # Check for data-utime attribute (Unix timestamp)
                if elem.get("data-utime"):
                    timestamp = int(elem.get("data-utime"))
                    return datetime.fromtimestamp(timestamp)

                # Check for datetime attribute
                if elem.get("datetime"):
                    return datetime.fromisoformat(
                        elem.get("datetime").replace("Z", "+00:00")
                    )

        except Exception as e:
            logger.error(f"Error extracting timestamp: {e}")

        return None

    def extract_engagement(self, post_element) -> Dict[str, int]:
        """Extract engagement metrics (likes, comments, shares)"""
        engagement = {"likes": 0, "comments": 0, "shares": 0}

        try:
            # Look for engagement text
            text = post_element.get_text()

            # Extract likes
            like_match = re.search(r"([\d,]+)\s*(?:likes?|thích)", text, re.IGNORECASE)
            if like_match:
                try:
                    engagement["likes"] = int(like_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            # Extract comments
            comment_match = re.search(
                r"([\d,]+)\s*(?:comments?|bình luận)", text, re.IGNORECASE
            )
            if comment_match:
                try:
                    engagement["comments"] = int(
                        comment_match.group(1).replace(",", "")
                    )
                except ValueError:
                    pass

            # Extract shares
            share_match = re.search(
                r"([\d,]+)\s*(?:shares?|chia sẻ)", text, re.IGNORECASE
            )
            if share_match:
                try:
                    engagement["shares"] = int(share_match.group(1).replace(",", ""))
                except ValueError:
                    pass

        except Exception as e:
            logger.error(f"Error extracting engagement: {e}")

        return engagement

    def extract_post_url(self, post_element) -> str:
        """Extract direct URL to the post"""
        try:
            links = post_element.find_all("a", href=True)
            for link in links:
                href = link["href"]
                # Exclude links that are clearly for comments or individual profiles
                if "comment_id=" in href or "reply_comment_id=" in href:
                    continue

                if any(
                    pattern in href
                    for pattern in ["/permalink/", "/posts/", "story_fbid=", "/videos/"]
                ):
                    # Make sure it's a full URL
                    if not href.startswith("http"):
                        if href.startswith("/"):
                            href = "https://www.facebook.com" + href
                        else:
                            href = "https://www.facebook.com/" + href

                    # Essential parameters to keep (exclude tracking and comment IDs)
                    keep_params = ["story_fbid", "id", "fbid", "set", "v"]

                    if "?" in href:
                        base_url, query = href.split("?", 1)
                        params = query.split("&")
                        filtered_params = [
                            p
                            for p in params
                            if any(p.startswith(k + "=") for k in keep_params)
                        ]

                        # If it has a comment_id, skip this link entirely
                        if any("comment_id=" in p for p in params):
                            continue

                        if filtered_params:
                            return f"{base_url}?{'&'.join(filtered_params)}"
                        return base_url

                    return href
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
                logger.debug("extract_post_id failed")
                return None

            # Extract all available data
            content = self.extract_content(post_element)
            media_urls = self.extract_media_urls(post_element)
            posted_at = self.extract_timestamp(post_element)
            engagement = self.extract_engagement(post_element)
            post_url = self.extract_post_url(post_element)

            # Only return post if we have at least some content or media
            if not content and not media_urls:
                logger.debug(f"Post {post_id} has no content and no media")
                return None

            post_data = {
                "post_id": post_id,
                "page_name": page_name,
                "content": content,
                "media_urls": media_urls,
                "posted_at": posted_at,
                "engagement": engagement,
                "post_url": post_url,
            }

            logger.debug(f"Parsed post: {post_id}")
            return post_data

        except Exception as e:
            logger.error(f"Error parsing post: {e}")
            return None

    def find_posts(self, html_content: str, page_name: str) -> List[Dict[str, Any]]:
        """
        Find and parse all posts in HTML content
        """
        self.parse_html(html_content)
        posts = []

        if self.soup.title:
            logger.info(f"Page Title: {self.soup.title.string}")

        if self._check_login_required():
            logger.warning("Facebook is requiring login to view this page.")

        # More specific selectors for actual posts
        post_selectors = [
            {"role": "article"},  # Main selector for most posts
            {"data-pagelet": lambda x: x and "FeedUnit" in x},
            {
                "data-pagelet": lambda x: x and "Component" in x
            },  # Sometimes Used in new layouts
            {"data-testid": "fbfeed_story"},
            {
                "class": lambda x: x and "x1yztbdb" in x and "x1n2onr6" in x
            },  # Common feed wrapper classes
        ]

        all_potential_elements = []
        for selector in post_selectors:
            elements = self.soup.find_all("div", selector)
            all_potential_elements.extend(elements)

        # Deduplicate by looking at hierarchy (don't pick a div if its parent is already picked)
        unique_posts = []
        for elem in all_potential_elements:
            # Check if this element is a child of any already identified post
            is_child = False
            for parent in all_potential_elements:
                if elem != parent and elem in parent.descendants:
                    is_child = True
                    break
            if not is_child:
                unique_posts.append(elem)

        logger.info(f"Found {len(unique_posts)} unique potential post elements")

        for post_elem in unique_posts:
            # 1. Broad exclusion: Skip elements that are clearly comments or nested UI
            if any(
                cls in str(post_elem.get("class", "")) for cls in ["comment", "reply"]
            ):
                continue

            # 2. Extract and parse
            post_data = self.parse_post(post_elem, page_name)
            if post_data:
                # Double check for minimal quality
                content = post_data["content"].strip()
                # A post is valid if it has content OR media
                if content or post_data["media_urls"]:
                    posts.append(post_data)
                else:
                    logger.debug(
                        f"Skipping post {post_data.get('post_id')} due to no content and no media"
                    )
            else:
                logger.debug("parse_post returned None for an element")

        logger.info(f"Successfully parsed {len(posts)} posts")
        return posts

    def _check_login_required(self) -> bool:
        """Check if Facebook is requiring login"""
        if not self.soup:
            return False

        # Check for common login-related elements
        login_indicators = [
            self.soup.find("form", {"id": "login_form"}),
            self.soup.find("input", {"name": "email"}),
            self.soup.find("input", {"name": "pass"}),
            self.soup.find(string=lambda text: text and "log in" in text.lower()),
        ]

        return any(login_indicators)
