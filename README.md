# Facebook Page Post Crawler

A robust Facebook page post crawler built with Python, Playwright, and MySQL. This system crawls Facebook pages, extracts posts with their metadata, and stores them in a database while avoiding detection.

## Features

- 🤖 **Automated Crawling**: Uses Playwright to simulate real user behavior
- 🔒 **Anti-Detection**: Implements stealth techniques to avoid Facebook checkpoints
- 💾 **Database Storage**: Stores posts in MySQL with duplicate detection
- 📊 **Dashboard**: Streamlit-based interface to view and manage crawled data
- ⏰ **Scheduled Tasks**: Celery-based periodic crawling
- 🐳 **Docker Support**: Fully containerized deployment

## Tech Stack

- **Python 3.11+**: Core programming language
- **Playwright**: Browser automation with stealth capabilities
- **BeautifulSoup4**: HTML parsing and data extraction
- **MySQL**: Database for structured data storage
- **Celery + Redis**: Task queue for scheduled crawling
- **Streamlit**: Web-based dashboard
- **Docker**: Containerization

## Installation

### Prerequisites

- Python 3.11 or higher
- MySQL 8.0+
- Redis 6.0+

### Setup

1. Clone the repository:
```bash
git clone https://github.com/tunnaduong/facebook-page-post-crawler.git
cd facebook-page-post-crawler
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
mysql -u root -p < database/schema.sql
```

## Usage

### Manual Crawling

Run a single crawl session:
```bash
# Using a page name (will be converted to https://www.facebook.com/page_name)
python src/crawler.py --page "microsoft"

# Using a full Facebook page URL
python src/crawler.py --page "https://www.facebook.com/microsoft"
```

### Scheduled Crawling

Start the Celery worker:
```bash
celery -A src.tasks worker --loglevel=info
```

Start the Celery beat scheduler:
```bash
celery -A src.tasks beat --loglevel=info
```

### Dashboard

Launch the Streamlit dashboard:
```bash
streamlit run src/dashboard.py
```

## Docker Deployment

Build and run with Docker Compose:
```bash
docker-compose up -d
```

This will start:
- MySQL database
- Redis server
- Celery worker
- Celery beat scheduler
- Streamlit dashboard

## Project Structure

```
facebook-page-post-crawler/
├── src/
│   ├── crawler.py          # Main crawler logic
│   ├── parser.py           # HTML parsing with BeautifulSoup
│   ├── database.py         # Database operations
│   ├── tasks.py            # Celery tasks
│   ├── dashboard.py        # Streamlit dashboard
│   └── config.py           # Configuration management
├── database/
│   └── schema.sql          # Database schema
├── cookies/                # Stored browser cookies
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This file
```

## Anti-Detection Features

1. **Cookie Persistence**: Login once and reuse cookies
2. **User-Agent Spoofing**: Uses playwright-stealth to appear as a real browser
3. **Random Delays**: Natural timing between actions
4. **Scrolling Behavior**: Mimics human scrolling patterns
5. **Proxy Support**: Optional residential proxy integration

## Database Schema

The `fb_posts` table stores:
- `post_id`: Unique Facebook post identifier
- `page_name`: Name of the Facebook page
- `content`: Post text content
- `media_urls`: JSON array of image/video URLs
- `posted_at`: When the post was published
- `crawled_at`: When the post was crawled
- `engagement`: JSON object with likes, comments, shares

## Troubleshooting

### No Posts Found (0 posts crawled)

If the crawler is finding 0 posts, try these solutions:

1. **Login Required**: Most Facebook pages require authentication to view posts
   ```bash
   # Save HTML for debugging
   python -m src.crawler --page "URL" --debug-html
   
   # The HTML will be saved to /tmp/facebook_crawler_debug/
   # Check if it shows a login page
   ```

2. **Use Authentication**:
   - Set `FB_EMAIL` and `FB_PASSWORD` in your `.env` file
   - Or manually login and save cookies:
     ```bash
     # Run without headless mode to login manually
     python -m src.crawler --page "URL"
     # Login in the browser window, then the cookies will be saved
     ```

3. **Profile vs Page URLs**:
   - Use Facebook Page URLs (e.g., `https://www.facebook.com/pagename`)
   - Profile URLs (`profile.php?id=...`) may require friendship/following and have different HTML structure

4. **Check Facebook Blocks**:
   - Facebook may block or limit automated access
   - Try with a different IP address or use proxies
   - Add delays between requests

5. **HTML Structure Changes**:
   - Facebook frequently updates their HTML
   - Use `--debug-html` to inspect the actual HTML structure
   - Update parser selectors if needed

### Common Issues

**"No cookie file found"**: This is normal on first run. The crawler will work without cookies but may have limited access.

**Browser won't start**: Make sure Playwright browsers are installed:
```bash
playwright install chromium
```

**Database connection errors**: Verify MySQL is running and credentials in `.env` are correct.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational purposes only. Please respect Facebook's Terms of Service and use responsibly.

## Disclaimer

This tool is intended for research and educational purposes. Users are responsible for complying with Facebook's Terms of Service and applicable laws. The authors are not responsible for misuse of this software.
