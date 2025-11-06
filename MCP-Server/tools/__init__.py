from .url_scraper.url_scraper_tool import newsletter_scrape, single_URL_scrape
from .data_analysis.forecast import forecast_tariffs
from .gmail_sender.gmail_tool import send_email_logic
from .article_analyzer.article_analyzer_tool import analyze
from .historical_viewer.historical_viewer_tool import get_historical_data

# Update __all__ to include all functions
__all__ = [
    "newsletter_scrape",
    "single_URL_scrape",
    "forecast_tariffs",
    "send_email_logic",
    "analyze",
    "get_historical_data", # Add this
]