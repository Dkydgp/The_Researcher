import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration for news fetcher"""
    
    # Project Root and Paths
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Vector Database
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(PROJECT_ROOT, "chroma_db"))
    COLLECTION_NAME = "economic_news"
    
    # Jina AI Embedding API
    JINA_API_KEY = os.getenv("JINA_API_KEY", "")
    JINA_API_URL = os.getenv("JINA_API_URL", "https://api.jina.ai/v1/embeddings")
    JINA_MODEL = os.getenv("JINA_MODEL", "jina-embeddings-v2-base-en")
    
    # RSS Feeds - Economic Times
    ECONOMIC_TIMES_FEEDS = {
        "top_stories": os.getenv("ET_TOP_STORIES", "https://economictimes.indiatimes.com/rssfeedstopstories.cms"),
        "markets": os.getenv("ET_MARKETS", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
        "stocks": os.getenv("ET_STOCKS", "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"),
        "economy": os.getenv("ET_ECONOMY", "https://economictimes.indiatimes.com/news/economy/rssfeeds/12865539.cms"),
        "companies": os.getenv("ET_COMPANIES", "https://economictimes.indiatimes.com/news/company/corporate-trends/rssfeeds/13357270.cms"),
    }
    
    # RSS Feeds - MoneyControl
    MONEYCONTROL_FEEDS = {
        "markets": os.getenv("MONEYCONTROL_MARKETS", "https://www.moneycontrol.com/rss/marketreports.xml"),
    }
    
    # RSS Feeds - Global/India
    GLOBAL_FEEDS = {
        "investing_india": "https://in.investing.com/rss/news.rss",
        "bloomberg_markets": "https://feeds.bloomberg.com/markets/news.rss"
    }
    
    # All feeds combined
    ALL_FEEDS = {
        **{f"moneycontrol_{k}": v for k, v in MONEYCONTROL_FEEDS.items()},
        **{f"economic_times_{k}": v for k, v in ECONOMIC_TIMES_FEEDS.items()},
        **GLOBAL_FEEDS
    }
    
    # Fetching Settings
    MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", "50"))
    FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))

config = Config()
