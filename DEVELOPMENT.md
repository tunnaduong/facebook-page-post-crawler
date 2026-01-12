# Development Guide

## Project Structure

```
facebook-page-post-crawler/
├── src/                      # Source code
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── crawler.py           # Main crawler with Playwright
│   ├── parser.py            # HTML parsing with BeautifulSoup
│   ├── database.py          # Database operations
│   ├── tasks.py             # Celery tasks
│   └── dashboard.py         # Streamlit dashboard
├── database/                 # Database files
│   └── schema.sql           # MySQL schema
├── cookies/                  # Stored browser cookies
├── logs/                     # Application logs
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # Docker image definition
├── requirements.txt          # Python dependencies
├── setup.sh                  # Setup script
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation
```

## Development Setup

1. Clone the repository
2. Run setup script: `./setup.sh`
3. Configure environment variables in `.env`
4. Initialize database: `mysql -u root -p < database/schema.sql`

## Running Components

### Crawler (Manual)
```bash
python src/crawler.py --page <page_url> --scrolls 10
```

### Celery Worker
```bash
celery -A src.tasks worker --loglevel=info
```

### Celery Beat (Scheduler)
```bash
celery -A src.tasks beat --loglevel=info
```

### Dashboard
```bash
streamlit run src/dashboard.py
```

## Development Workflow

1. **Phase 1: Basic Crawling**
   - Implement browser automation with Playwright
   - Handle cookie management
   - Test on a public Facebook page

2. **Phase 2: Data Extraction**
   - Parse HTML with BeautifulSoup
   - Extract post content, media, timestamps
   - Extract engagement metrics

3. **Phase 3: Database Integration**
   - Connect to MySQL
   - Implement duplicate checking
   - Save posts to database

4. **Phase 4: Task Scheduling**
   - Set up Celery workers
   - Configure periodic tasks
   - Test scheduled crawling

5. **Phase 5: Dashboard**
   - Create Streamlit interface
   - Display posts and statistics
   - Add filtering and search

6. **Phase 6: Anti-Detection**
   - Implement random delays
   - Add natural scrolling
   - Configure stealth mode

7. **Phase 7: Dockerization**
   - Create Docker images
   - Set up docker-compose
   - Test full deployment

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing

### Manual Testing
Test each component individually:
```bash
# Test database connection
python -c "from src.database import Database; db = Database(); db.connect()"

# Test parser
python -c "from src.parser import FacebookParser; parser = FacebookParser()"

# Test crawler with a public page
python src/crawler.py --page https://www.facebook.com/public_page --no-save
```

## Anti-Detection Best Practices

1. **Cookie Management**: Login once, save cookies, reuse for future sessions
2. **Random Delays**: Add 2-5 second delays between actions
3. **Natural Scrolling**: Scroll gradually, not all at once
4. **User Agent**: Use realistic browser fingerprint
5. **Rate Limiting**: Don't crawl too frequently (recommend 1+ hour intervals)
6. **Proxy Rotation**: Use residential proxies for large-scale crawling

## Troubleshooting

### Issue: Browser won't start
- Solution: Run `playwright install chromium` again
- Check system dependencies: `playwright install-deps chromium`

### Issue: Can't connect to database
- Verify MySQL is running
- Check credentials in `.env`
- Ensure database exists: `CREATE DATABASE facebook_crawler;`

### Issue: Facebook checkpoint/login required
- Delete old cookies
- Login manually with browser
- Save new cookies
- Use longer delays between requests

### Issue: Celery tasks not running
- Verify Redis is running
- Check Celery worker logs
- Ensure tasks are registered properly

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Security Notes

- Never commit `.env` file or cookies
- Store credentials securely
- Use environment variables for sensitive data
- Respect Facebook's Terms of Service
- Implement rate limiting to avoid bans

## Performance Optimization

1. **Database Indexing**: Already implemented on key columns
2. **Connection Pooling**: Consider implementing for high-volume scenarios
3. **Caching**: Cache page metadata to reduce database queries
4. **Parallel Processing**: Use Celery for concurrent page crawling
5. **Headless Mode**: Always use headless=True in production

## Monitoring

Monitor these metrics:
- Crawl success rate
- Number of posts found vs saved
- Time per crawl session
- Database growth
- Error rates

## Future Enhancements

- [ ] Support for Facebook groups
- [ ] Image download and local storage
- [ ] Sentiment analysis on post content
- [ ] Export to CSV/JSON
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-account support
- [ ] Comment crawling
