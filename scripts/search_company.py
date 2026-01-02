"""
Search company-specific news from filtered database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from src.utils.filter_companies import CompanyNewsFilter
from src.utils.config import config

def search_company(company_name: str, query: str = None, limit: int = 10):
    """Search news for a specific company"""
    
    # Connect to filtered collection
    client = chromadb.PersistentClient(
        path=config.CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection("top5_nifty_news")
    except:
        print("❌ Filtered database not found!")
        print("Run: python filter_companies.py first")
        return
    
    print(f"\n🔍 Searching news for: {company_name}")
    print("=" * 60)
    
    if query:
        # Connect to main DB to get embedding logic
        from src.core.vector_db import VectorDB
        vdb = VectorDB()
        query_embedding = vdb._generate_embedding(query)
        
        # Semantic search with company filter
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"company": company_name}
        )
        
        if not results['ids'] or len(results['ids'][0]) == 0:
            print("No results found")
            return
        
        for i in range(len(results['ids'][0])):
            print(f"\n{i+1}. {results['metadatas'][0][i]['title']}")
            print(f"   Source: {results['metadatas'][0][i]['source']}")
            print(f"   Date: {results['metadatas'][0][i]['published_date']}")
            print(f"   URL: {results['metadatas'][0][i]['url']}")
            if 'distances' in results:
                print(f"   Similarity: {1 - results['distances'][0][i]:.2%}")
    else:
        # Get all articles for company
        results = collection.get(
            where={"company": company_name},
            limit=limit
        )
        
        if not results['ids']:
            print("No articles found for this company")
            return
        
        print(f"Found {len(results['ids'])} articles\n")
        
        for i in range(len(results['ids'])):
            print(f"\n{i+1}. {results['metadatas'][i]['title']}")
            print(f"   Source: {results['metadatas'][i]['source']}")
            print(f"   Date: {results['metadatas'][i]['published_date']}")
            print(f"   URL: {results['metadatas'][i]['url']}")

def show_stats():
    """Show statistics for filtered database"""
    client = chromadb.PersistentClient(
        path=config.CHROMA_DB_PATH,
        settings=Settings(anonymized_telemetry=False)
    )
    
    try:
        collection = client.get_collection("top5_nifty_news")
    except:
        print("❌ Filtered database not found!")
        print("Run: python filter_companies.py first")
        return
    
    print("\n📊 TOP 5 NIFTY NEWS DATABASE")
    print("=" * 60)
    
    total = collection.count()
    print(f"\nTotal Articles: {total}")
    
    print("\nBy Company:")
    for company in TOP_5_NIFTY.keys():
        results = collection.get(where={"company": company})
        count = len(results['ids'])
        print(f"  • {company}: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python search_company.py stats")
        print("  python search_company.py <company_name>")
        print("  python search_company.py <company_name> <search_query>")
        print("\nCompanies:")
        for company in TOP_5_NIFTY.keys():
            print(f"  - {company}")
        sys.exit(1)
    
    if sys.argv[1] == "stats":
        show_stats()
    else:
        company = sys.argv[1]
        query = sys.argv[2] if len(sys.argv) > 2 else None
        search_company(company, query)
