"""
Utility script to add Facebook pages to monitor
"""
import sys
import argparse
from src.database import Database
from src.config import Config

def add_page(page_name: str, page_url: str, crawl_frequency: int = 60):
    """
    Add a Facebook page to the monitoring list
    
    Args:
        page_name: Identifier for the page
        page_url: Full URL to the Facebook page
        crawl_frequency: How often to crawl in minutes (default: 60)
    """
    db = Database()
    
    try:
        db.connect()
        
        query = """
        INSERT INTO fb_pages (page_name, page_url, crawl_frequency_minutes, is_active)
        VALUES (%s, %s, %s, TRUE)
        ON DUPLICATE KEY UPDATE 
            page_url = VALUES(page_url),
            crawl_frequency_minutes = VALUES(crawl_frequency_minutes),
            is_active = TRUE,
            updated_at = CURRENT_TIMESTAMP
        """
        
        db.execute_query(query, (page_name, page_url, crawl_frequency))
        print(f"✓ Successfully added/updated page: {page_name}")
        print(f"  URL: {page_url}")
        print(f"  Crawl frequency: {crawl_frequency} minutes")
        
    except Exception as e:
        print(f"✗ Error adding page: {e}")
        sys.exit(1)
    finally:
        db.disconnect()


def list_pages():
    """List all monitored pages"""
    db = Database()
    
    try:
        db.connect()
        
        query = """
        SELECT page_name, page_url, is_active, crawl_frequency_minutes, last_crawled_at
        FROM fb_pages
        ORDER BY page_name
        """
        
        pages = db.fetch_query(query)
        
        if not pages:
            print("No pages found in the database.")
            return
        
        print("\nMonitored Facebook Pages:")
        print("=" * 100)
        print(f"{'Page Name':<30} {'Status':<10} {'Frequency':<15} {'Last Crawled':<25}")
        print("-" * 100)
        
        for page in pages:
            status = "Active" if page['is_active'] else "Inactive"
            frequency = f"{page['crawl_frequency_minutes']} min"
            last_crawled = page['last_crawled_at'].strftime("%Y-%m-%d %H:%M") if page['last_crawled_at'] else "Never"
            
            print(f"{page['page_name']:<30} {status:<10} {frequency:<15} {last_crawled:<25}")
        
        print("=" * 100)
        print(f"Total pages: {len(pages)}")
        
    except Exception as e:
        print(f"✗ Error listing pages: {e}")
        sys.exit(1)
    finally:
        db.disconnect()


def remove_page(page_name: str):
    """
    Deactivate a page from monitoring
    
    Args:
        page_name: Name of the page to deactivate
    """
    db = Database()
    
    try:
        db.connect()
        
        query = "UPDATE fb_pages SET is_active = FALSE WHERE page_name = %s"
        db.execute_query(query, (page_name,))
        
        print(f"✓ Successfully deactivated page: {page_name}")
        
    except Exception as e:
        print(f"✗ Error removing page: {e}")
        sys.exit(1)
    finally:
        db.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Manage Facebook pages to monitor')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add page command
    add_parser = subparsers.add_parser('add', help='Add a page to monitor')
    add_parser.add_argument('name', help='Page name identifier')
    add_parser.add_argument('url', help='Facebook page URL')
    add_parser.add_argument('--frequency', type=int, default=60, 
                          help='Crawl frequency in minutes (default: 60)')
    
    # List pages command
    list_parser = subparsers.add_parser('list', help='List all monitored pages')
    
    # Remove page command
    remove_parser = subparsers.add_parser('remove', help='Deactivate a page')
    remove_parser.add_argument('name', help='Page name to deactivate')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        add_page(args.name, args.url, args.frequency)
    elif args.command == 'list':
        list_pages()
    elif args.command == 'remove':
        remove_page(args.name)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
