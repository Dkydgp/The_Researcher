#!/usr/bin/env python3
"""
Economic News Fetcher with Vector Database
Fetches news from RSS feeds and enables semantic search
"""

import sys
import argparse
from src.collectors.news_fetcher import NewsFetcher
from src.core.vector_db import VectorDB
from src.collectors.price_fetcher import PriceFetcher
from src.collectors.screener_fetcher import ScreenerFetcher

def fetch_news():
    """Fetch latest news from all RSS feeds"""
    fetcher = NewsFetcher()
    fetcher.fetch_all()

def fetch_prices():
    """Fetch daily OHLC prices"""
    fetcher = PriceFetcher()
    fetcher.fetch_today_prices()

def fetch_fundamentals():
    """Fetch fundamental data from Screener.in"""
    fetcher = ScreenerFetcher()
    fetcher.fetch_fundamentals()

def search_news(query: str, limit: int = 10):
    """Search news semantically"""
    print(f"\nSearching for: '{query}'")
    print("=" * 60)
    
    db = VectorDB()
    results = db.search(query, n_results=limit)
    
    if not results:
        print("No results found")
        return
    
    for i, article in enumerate(results, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']} | Date: {article['published_date']}")
        print(f"   URL: {article['url']}")
        if article['distance'] is not None:
            print(f"   Similarity: {1 - article['distance']:.2%}")
        print(f"   {article['snippet']}")

def show_stats():
    """Show database statistics"""
    print("\nDATABASE STATISTICS")
    print("=" * 60)
    
    db = VectorDB()
    stats = db.get_stats()
    
    print(f"\nTotal Articles: {stats['total_articles']}")
    
    if stats['by_source']:
        print("\nBy Source:")
        for source, count in stats['by_source'].items():
            print(f"  • {source}: {count}")

def clear_database():
    """Clear all data"""
    print("\nWARNING: This will delete all stored articles!")
    confirm = input("Type 'yes' to confirm: ")
    
    if confirm.lower() == 'yes':
        db = VectorDB()
        db.clear_all()
        print("Database cleared")
    else:
        print("Cancelled")

def main():
    parser = argparse.ArgumentParser(
        description='Economic News Fetcher with Vector Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py fetch                    # Fetch latest news
  python main.py search "stock market"    # Search news
  python main.py stats                    # Show statistics
  python main.py clear                    # Clear database
        """
    )
    
    parser.add_argument(
        'command',
        choices=['fetch', 'search', 'stats', 'clear', 'prices', 'fundamentals'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'query',
        nargs='?',
        help='Search query (for search command)'
    )
    
    parser.add_argument(
        '-n', '--limit',
        type=int,
        default=10,
        help='Number of search results (default: 10)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'fetch':
            fetch_news()
        elif args.command == 'prices':
            fetch_prices()
        elif args.command == 'fundamentals':
            fetch_fundamentals()
        elif args.command == 'search':
            if not args.query:
                print("Error: search command requires a query")
                sys.exit(1)
            search_news(args.query, args.limit)
        elif args.command == 'stats':
            show_stats()
        elif args.command == 'clear':
            clear_database()
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
