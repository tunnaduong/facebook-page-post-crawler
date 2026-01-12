"""
Celery tasks for scheduled Facebook page crawling
"""
import logging
from celery import Celery
from celery.schedules import crontab

from src.config import Config
from src.crawler import FacebookCrawler
from src.database import Database

logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery(
    'facebook_crawler',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=1,
)


@app.task(name='crawl_page')
def crawl_page_task(page_url: str, page_name: str = None, scrolls: int = 5):
    """
    Celery task to crawl a Facebook page
    
    Args:
        page_url: URL of the Facebook page
        page_name: Name identifier for the page
        scrolls: Number of scroll iterations
        
    Returns:
        Dictionary with crawl results
    """
    logger.info(f"Starting crawl task for {page_url}")
    
    try:
        crawler = FacebookCrawler(headless=True)
        results = crawler.run(
            page_url=page_url,
            page_name=page_name,
            scrolls=scrolls,
            use_cookies=True,
            save_to_db=True
        )
        
        logger.info(f"Crawl task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in crawl task: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@app.task(name='crawl_all_active_pages')
def crawl_all_active_pages_task():
    """
    Celery task to crawl all active pages from database
    
    Returns:
        Dictionary with summary of tasks created
    """
    logger.info("Starting crawl task for all active pages")
    
    db = Database()
    
    try:
        db.connect()
        active_pages = db.get_active_pages()
        
        logger.info(f"Found {len(active_pages)} active pages to crawl")
        
        # Queue individual crawl tasks (not recursive, just scheduling)
        task_count = 0
        for page in active_pages:
            page_url = page['page_url']
            page_name = page['page_name']
            
            logger.info(f"Queueing crawl for page: {page_name}")
            
            # Queue crawl task (will be executed by worker pool)
            crawl_page_task.delay(page_url, page_name, 5)
            task_count += 1
        
        return {
            'success': True,
            'pages_queued': task_count
        }
        
    except Exception as e:
        logger.error(f"Error in crawl all pages task: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        db.disconnect()


# Periodic task schedule
app.conf.beat_schedule = {
    'crawl-all-pages-hourly': {
        'task': 'crawl_all_active_pages',
        'schedule': crontab(minute=0),  # Run every hour at minute 0
    },
}


if __name__ == '__main__':
    # Run worker
    app.worker_main()
