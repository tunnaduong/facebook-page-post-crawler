# Example configuration for adding sample Facebook pages

# Add some example public pages to monitor
# Modify these with actual Facebook pages you want to crawl

# Example: News pages
python manage_pages.py add "BBC News" "https://www.facebook.com/bbcnews" --frequency 60

# Example: Tech companies
python manage_pages.py add "Microsoft" "https://www.facebook.com/Microsoft" --frequency 120

# Example: Sports
python manage_pages.py add "FIFA" "https://www.facebook.com/fifa" --frequency 180

# List all pages
python manage_pages.py list

# To remove a page from monitoring:
# python manage_pages.py remove "BBC News"
