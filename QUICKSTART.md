# Quick Start Guide

This guide will help you get the Facebook Page Post Crawler up and running quickly.

## Prerequisites

- Python 3.11+
- MySQL 8.0+
- Redis 6.0+ (for scheduled tasks)
- Git

## Installation (Local Development)

### 1. Clone and Setup

```bash
git clone https://github.com/tunnaduong/facebook-page-post-crawler.git
cd facebook-page-post-crawler
./setup.sh
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

Key settings to configure:
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` - MySQL credentials
- `FB_EMAIL`, `FB_PASSWORD` - Facebook login (optional, for manual login)
- `HEADLESS` - Set to `false` for first run to login manually

### 3. Setup Database

```bash
# Login to MySQL
mysql -u root -p

# Run schema
mysql -u root -p < database/schema.sql
```

### 4. First Run - Manual Crawl

Activate the virtual environment and run a test crawl:

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Crawl using a full URL
python src/crawler.py --page "https://www.facebook.com/microsoft" --scrolls 3

# Or crawl using just the page name (will be converted to full URL)
python src/crawler.py --page "microsoft" --scrolls 3
```

This will:
- Open a browser window
- Navigate to the page
- Scroll 3 times to load posts
- Parse and display posts in console
- Save to database (if configured)

## Installation (Docker)

For production deployment with Docker:

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- MySQL database
- Redis server
- Celery worker (for task processing)
- Celery beat (for scheduling)
- Streamlit dashboard (accessible at http://localhost:8501)

### 3. Add Pages to Monitor

```bash
# Add a page to the monitoring list
docker-compose exec celery_worker python manage_pages.py add "BBC" "https://www.facebook.com/bbcnews" --frequency 60

# List monitored pages
docker-compose exec celery_worker python manage_pages.py list
```

### 4. View Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

## Usage Examples

### Manual Crawling

```bash
# Basic crawl with page name
python src/crawler.py --page "microsoft"

# Basic crawl with full URL
python src/crawler.py --page "https://www.facebook.com/microsoft"

# Crawl with more scrolls (load more posts)
python src/crawler.py --page "https://www.facebook.com/microsoft" --scrolls 10

# Crawl without saving to database (testing)
python src/crawler.py --page "microsoft" --no-save

# Crawl in headless mode
python src/crawler.py --page "https://www.facebook.com/microsoft" --headless
```

### Managing Pages

```bash
# Add a page to monitor
python manage_pages.py add "MyPage" "https://www.facebook.com/mypage" --frequency 120

# List all pages
python manage_pages.py list

# Deactivate a page
python manage_pages.py remove "MyPage"
```

### Scheduled Crawling

```bash
# Terminal 1: Start Redis (if not using Docker)
redis-server

# Terminal 2: Start Celery worker
celery -A src.tasks worker --loglevel=info

# Terminal 3: Start Celery beat scheduler
celery -A src.tasks beat --loglevel=info
```

### Dashboard

```bash
streamlit run src/dashboard.py
```

Then open http://localhost:8501 in your browser.

## First-Time Login

For the first crawl, you may need to login to Facebook:

1. Set `HEADLESS=false` in `.env`
2. Run crawler: `python src/crawler.py --page <url>`
3. A browser window will open
4. Login manually if prompted
5. The crawler will save cookies automatically
6. Future runs will use saved cookies

## Troubleshooting

### Issue: "Browser executable not found"
```bash
playwright install chromium
playwright install-deps chromium
```

### Issue: "Can't connect to database"
```bash
# Check MySQL is running
sudo systemctl status mysql

# Test connection
mysql -u root -p -e "SHOW DATABASES;"
```

### Issue: "Facebook checkpoint/security check"
- Delete cookies folder: `rm -rf cookies/*`
- Set `HEADLESS=false` in `.env`
- Login manually when browser opens
- Add longer delays: `RANDOM_DELAY_MIN=5`, `RANDOM_DELAY_MAX=10`

### Issue: "No posts found"
- Facebook's HTML structure changes frequently
- The page may require login to view posts
- Try with a different public page first
- Check parser.py selectors may need updating

## Next Steps

1. **Test the crawler** on a few public pages
2. **Add pages to monitor** using `manage_pages.py`
3. **Set up scheduled crawling** with Celery
4. **Monitor results** through the Streamlit dashboard
5. **Adjust delays and intervals** to avoid detection
6. **Scale up** using Docker for production

## Important Notes

⚠️ **Respect Facebook's Terms of Service**
- Use responsibly and ethically
- Don't crawl too aggressively
- Respect rate limits
- Only crawl public content

⚠️ **Security**
- Never commit `.env` or `cookies/` to version control
- Use strong database passwords
- Keep credentials secure

⚠️ **Performance**
- Start with few pages and low frequency
- Monitor database size
- Use headless mode in production
- Consider proxy rotation for large-scale crawling

## Support

For issues, please check:
1. DEVELOPMENT.md for detailed development guide
2. README.md for comprehensive documentation
3. GitHub Issues for community support
