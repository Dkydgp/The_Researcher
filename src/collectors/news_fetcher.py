import feedparser
import requests
from datetime import datetime
from typing import List, Dict
from bs4 import BeautifulSoup
from src.utils.config import config
from src.core.vector_db import VectorDB

class NewsFetcher:
    """Fetch news from RSS feeds and store in vector database"""
    
    def __init__(self):
        self.db = VectorDB()
        self.feeds = config.ALL_FEEDS
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _parse_date(self, entry: Dict) -> str:
        """Parse and format date from entry"""
        # Try published_parsed first (struct_time)
        dt_parsed = entry.get('published_parsed')
        if dt_parsed:
            try:
                dt = datetime(*dt_parsed[:6])
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # Try raw published string
        dt_str = entry.get('published') or entry.get('updated')
        if dt_str:
            try:
                # Common RSS date formats
                import dateutil.parser
                dt = dateutil.parser.parse(dt_str)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # Fallback to current time
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def fetch_feed(self, feed_name: str, feed_url: str) -> int:
        """Fetch articles from a single RSS feed"""
        print(f"\nFetching from {feed_name}...")
        print(f"URL: {feed_url}")
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                print(f"  Warning: No entries found in feed")
                return 0
            
            added_count = 0
            
            # Process each entry
            for entry in feed.entries[:config.MAX_ARTICLES_PER_FEED]:
                try:
                    # Extract article data
                    title = self._clean_text(entry.get('title', ''))
                    description = self._clean_text(
                        entry.get('description', '') or 
                        entry.get('summary', '')
                    )
                    url = entry.get('link', '')
                    published_date = self._parse_date(entry)
                    
                    # Skip if missing essential data
                    if not title or not url:
                        continue
                    
                    # Determine source
                    if 'moneycontrol' in feed_name:
                        source = 'MoneyControl'
                    elif 'economic_times' in feed_name:
                        source = 'Economic Times'
                    else:
                        source = feed_name
                    
                    # Extract category from feed name
                    category = feed_name.split('_')[-1] if '_' in feed_name else ''
                    
                    # Add to database
                    if self.db.add_article(
                        title=title,
                        description=description,
                        url=url,
                        source=source,
                        published_date=published_date,
                        category=category
                    ):
                        added_count += 1
                
                except Exception as e:
                    print(f"  Error processing entry: {e}")
                    continue
            
            print(f"  Added {added_count} new articles from {feed_name}")
            return added_count
        
        except Exception as e:
            print(f"  Error fetching feed: {e}")
            return 0
    
    def fetch_all(self) -> Dict[str, int]:
        """Fetch from all configured RSS feeds"""
        print("=" * 60)
        print("FETCHING NEWS FROM RSS FEEDS")
        print("=" * 60)
        
        results = {}
        total_added = 0
        
        for feed_name, feed_url in self.feeds.items():
            added = self.fetch_feed(feed_name, feed_url)
            results[feed_name] = added
            total_added += added
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: Added {total_added} new articles")
        print("=" * 60)
        
        return results

if __name__ == "__main__":
    # Test the fetcher
    fetcher = NewsFetcher()
    fetcher.fetch_all()
