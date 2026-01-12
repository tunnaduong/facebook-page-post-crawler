"""
Streamlit Dashboard for Facebook Page Post Crawler
"""
import json
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from src.database import Database
from src.config import Config

# Page configuration
st.set_page_config(
    page_title="Facebook Page Crawler Dashboard",
    page_icon="📊",
    layout="wide"
)


# Helper functions
def parse_json_field(json_field):
    """Parse JSON field from database (handles both string and dict)"""
    if not json_field:
        return None
    if isinstance(json_field, str):
        try:
            return json.loads(json_field)
        except:
            return None
    return json_field


# Initialize database connection
@st.cache_resource
def get_database():
    """Get database connection"""
    db = Database()
    db.connect()
    return db


def format_engagement(engagement_json):
    """Format engagement JSON for display"""
    engagement = parse_json_field(engagement_json)
    if not engagement:
        return "N/A"
    return f"👍 {engagement.get('likes', 0)} | 💬 {engagement.get('comments', 0)} | 🔄 {engagement.get('shares', 0)}"


def main():
    """Main dashboard application"""
    
    st.title("📊 Facebook Page Post Crawler Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("Configuration")
    db = get_database()
    
    # Overview metrics
    st.header("📈 Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get statistics
    try:
        total_posts_query = "SELECT COUNT(*) as count FROM fb_posts"
        total_posts = db.fetch_query(total_posts_query)[0]['count']
        
        pages_query = "SELECT COUNT(DISTINCT page_name) as count FROM fb_posts"
        total_pages = db.fetch_query(pages_query)[0]['count']
        
        recent_query = "SELECT COUNT(*) as count FROM fb_posts WHERE crawled_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)"
        posts_24h = db.fetch_query(recent_query)[0]['count']
        
        last_crawl_query = "SELECT MAX(crawled_at) as last_crawl FROM fb_posts"
        last_crawl_result = db.fetch_query(last_crawl_query)[0]
        last_crawl = last_crawl_result['last_crawl'] if last_crawl_result['last_crawl'] else "Never"
        
        col1.metric("Total Posts", total_posts)
        col2.metric("Pages Monitored", total_pages)
        col3.metric("Posts (24h)", posts_24h)
        col4.metric("Last Crawl", last_crawl if last_crawl == "Never" else last_crawl.strftime("%Y-%m-%d %H:%M"))
        
    except Exception as e:
        st.error(f"Error fetching statistics: {e}")
    
    st.markdown("---")
    
    # Filter section
    st.header("🔍 Filter Posts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Get list of pages
        try:
            pages_query = "SELECT DISTINCT page_name FROM fb_posts ORDER BY page_name"
            pages = db.fetch_query(pages_query)
            page_names = ["All Pages"] + [p['page_name'] for p in pages]
            selected_page = st.selectbox("Select Page", page_names)
        except Exception as e:
            st.error(f"Error fetching pages: {e}")
            selected_page = "All Pages"
    
    with col2:
        limit = st.slider("Number of posts to display", 10, 100, 50)
    
    # Fetch and display posts
    st.header("📝 Recent Posts")
    
    try:
        if selected_page == "All Pages":
            posts = db.get_recent_posts(limit=limit)
        else:
            posts = db.get_recent_posts(page_name=selected_page, limit=limit)
        
        if posts:
            # Convert to DataFrame for better display
            posts_data = []
            for post in posts:
                # Parse JSON fields using helper function
                media_urls = parse_json_field(post['media_urls'])
                engagement = parse_json_field(post['engagement'])
                
                posts_data.append({
                    'Page': post['page_name'],
                    'Post ID': post['post_id'],
                    'Content': post['content'][:100] + "..." if post['content'] and len(post['content']) > 100 else post['content'],
                    'Media Count': len(media_urls) if media_urls else 0,
                    'Engagement': format_engagement(engagement),
                    'Posted At': post['posted_at'].strftime("%Y-%m-%d %H:%M") if post['posted_at'] else "N/A",
                    'Crawled At': post['crawled_at'].strftime("%Y-%m-%d %H:%M") if post['crawled_at'] else "N/A",
                })
            
            df = pd.DataFrame(posts_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Detailed view
            st.subheader("📄 Post Details")
            post_ids = [p['post_id'] for p in posts]
            selected_post_id = st.selectbox("Select a post to view details", post_ids)
            
            if selected_post_id:
                selected_post = next(p for p in posts if p['post_id'] == selected_post_id)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Content:**")
                    st.write(selected_post['content'] or "No content")
                    
                    st.markdown("**URL:**")
                    if selected_post['post_url']:
                        st.markdown(f"[View on Facebook]({selected_post['post_url']})")
                    else:
                        st.write("N/A")
                
                with col2:
                    st.markdown("**Metadata:**")
                    st.write(f"Page: {selected_post['page_name']}")
                    st.write(f"Post ID: {selected_post['post_id']}")
                    
                    if selected_post['posted_at']:
                        st.write(f"Posted: {selected_post['posted_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    st.write(f"Crawled: {selected_post['crawled_at'].strftime('%Y-%m-%d %H:%M')}")
                
                # Media URLs
                media_urls = parse_json_field(selected_post['media_urls'])
                if media_urls:
                    st.markdown("**Media URLs:**")
                    for i, url in enumerate(media_urls, 1):
                        st.write(f"{i}. {url}")
                
                # Engagement
                engagement = parse_json_field(selected_post['engagement'])
                if engagement:
                    st.markdown("**Engagement:**")
                    ecol1, ecol2, ecol3 = st.columns(3)
                    ecol1.metric("Likes", engagement.get('likes', 0))
                    ecol2.metric("Comments", engagement.get('comments', 0))
                    ecol3.metric("Shares", engagement.get('shares', 0))
        else:
            st.info("No posts found")
            
    except Exception as e:
        st.error(f"Error fetching posts: {e}")
    
    st.markdown("---")
    
    # Crawl logs
    st.header("📋 Recent Crawl Logs")
    
    try:
        logs_query = """
        SELECT * FROM crawl_logs 
        ORDER BY started_at DESC 
        LIMIT 20
        """
        logs = db.fetch_query(logs_query)
        
        if logs:
            logs_data = []
            for log in logs:
                duration = "N/A"
                if log['finished_at'] and log['started_at']:
                    delta = log['finished_at'] - log['started_at']
                    duration = f"{delta.total_seconds():.0f}s"
                
                logs_data.append({
                    'Page': log['page_name'],
                    'Status': log['status'],
                    'Started': log['started_at'].strftime("%Y-%m-%d %H:%M"),
                    'Duration': duration,
                    'Found': log['posts_found'],
                    'New': log['posts_new'],
                    'Updated': log['posts_updated'],
                })
            
            df_logs = pd.DataFrame(logs_data)
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No crawl logs found")
            
    except Exception as e:
        st.error(f"Error fetching crawl logs: {e}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center'>
            <p>Facebook Page Post Crawler Dashboard | Built with Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    main()
