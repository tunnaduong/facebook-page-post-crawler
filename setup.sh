#!/bin/bash
# Setup script for Facebook Page Post Crawler

set -e

echo "================================================"
echo "Facebook Page Post Crawler - Setup Script"
echo "================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
playwright install chromium

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Create necessary directories
echo ""
echo "Creating necessary directories..."
mkdir -p cookies logs

echo ""
echo "================================================"
echo "Setup completed successfully!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Set up MySQL database:"
echo "   mysql -u root -p < database/schema.sql"
echo "3. Activate virtual environment:"
echo "   source venv/bin/activate"
echo "4. Run the crawler:"
echo "   python src/crawler.py --page <page_url>"
echo ""
