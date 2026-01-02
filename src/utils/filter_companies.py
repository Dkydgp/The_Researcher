"""
Filter news for top 5 Nifty companies
Creates a separate collection with only relevant company news
"""

from src.core.vector_db import VectorDB
from src.utils.config import config
import chromadb
from chromadb.config import Settings

# Top 10 Nifty companies with semantic search queries
TOP_5_NIFTY = {
    "Reliance Industries": {
        "keywords": ["reliance", "ril", "mukesh ambani", "jio", "reliance jio"],
        "semantic_queries": [
            "Reliance Industries business news",
            "telecom sector policy India",
            "oil and gas industry regulations",
            "retail sector India",
            "Jio telecommunications"
        ]
    },
    "TCS": {
        "keywords": ["tcs", "tata consultancy services"],
        "semantic_queries": [
            "TCS Tata Consultancy Services",
            "IT services industry India",
            "technology outsourcing policy",
            "software exports India"
        ]
    },
    "HDFC Bank": {
        "keywords": ["hdfc bank", "hdfc"],
        "semantic_queries": [
            "HDFC Bank news",
            "banking sector regulations India",
            "RBI monetary policy banks",
            "private sector banks India"
        ]
    },
    "Infosys": {
        "keywords": ["infosys", "infy"],
        "semantic_queries": [
            "Infosys company news",
            "IT industry policy India",
            "technology sector regulations",
            "software services India"
        ]
    },
    "ICICI Bank": {
        "keywords": ["icici bank", "icici"],
        "semantic_queries": [
            "ICICI Bank news",
            "banking regulations India",
            "RBI policy private banks",
            "financial sector India"
        ]
    },
    "Bharti Airtel": {
        "keywords": ["bharti airtel", "airtel", "bharti"],
        "semantic_queries": [
            "Airtel telecommunications news",
            "telecom sector India policy",
            "5G spectrum auction",
            "mobile network regulations"
        ]
    },
    "ITC": {
        "keywords": ["itc limited", "itc", "itc ltd"],
        "semantic_queries": [
            "ITC company news",
            "FMCG sector India",
            "tobacco regulations India",
            "hotel industry India"
        ]
    },
    "Wipro": {
        "keywords": ["wipro", "wipro limited"],
        "semantic_queries": [
            "Wipro IT services news",
            "technology consulting India",
            "software services sector",
            "IT outsourcing India"
        ]
    },
    "HCL Technologies": {
        "keywords": ["hcl technologies", "hcl tech", "hcl"],
        "semantic_queries": [
            "HCL Technologies news",
            "IT services India",
            "technology sector policy",
            "software engineering India"
        ]
    },
    "Bajaj Finance": {
        "keywords": ["bajaj finance", "bajaj finserv"],
        "semantic_queries": [
            "Bajaj Finance NBFC news",
            "non-banking financial companies India",
            "consumer finance regulations",
            "RBI NBFC policy"
        ]
    }
}

# Indices tracking
INDICES = {
    "NIFTY 50": {
        "ticker": "^NSEI",
        "keywords": ["nifty", "nifty 50", "nse index"],
        "semantic_queries": [
            "NIFTY 50 index movement",
            "Indian stock market overall",
            "NSE benchmark index"
        ]
    },
    "SENSEX": {
        "ticker": "^BSESN",
        "keywords": ["sensex", "bse sensex", "bombay stock exchange"],
        "semantic_queries": [
            "SENSEX index news",
            "BSE benchmark movement",
            "Mumbai stock market"
        ]
    }
}

class CompanyNewsFilter:
    """Filter and store news for specific companies"""
    
    def __init__(self):
        # Connect to main database
        self.main_db = VectorDB()
        
        # Create filtered collection
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Delete old filtered collection if exists
        try:
            self.client.delete_collection("top5_nifty_news")
        except:
            pass
        try:
            self.client.delete_collection("top10_nifty_news")
        except:
            pass
        
        # Create new filtered collection
        self.filtered_collection = self.client.create_collection(
            name="top10_nifty_news",
            metadata={"description": "News filtered for top 10 Nifty companies + indices"}
        )
        
        print("✓ Created filtered collection: top10_nifty_news")
    
    def is_company_relevant(self, text: str, keywords: list) -> bool:
        """Check if text mentions company keywords"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def get_semantic_relevance(self, article_text: str, company_queries: list, threshold: float = 0.35) -> float:
        """Check semantic relevance using vector similarity"""
        # Search for each semantic query
        max_similarity = 0.0
        
        for query in company_queries:
            results = self.main_db.collection.query(
                query_texts=[query],
                n_results=1,
                where_document={"$contains": article_text[:100]}  # Match by text snippet
            )
            
            if results['distances'] and len(results['distances'][0]) > 0:
                # Convert distance to similarity (lower distance = higher similarity)
                similarity = 1 - results['distances'][0][0]
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def filter_and_copy(self):
        """Filter news using hybrid approach: keywords + semantic similarity"""
        print("\n" + "=" * 60)
        print("FILTERING NEWS FOR TOP 10 NIFTY COMPANIES + INDICES")
        print("Using hybrid approach: Keywords + Semantic Analysis")
        print("=" * 60)
        
        # Get all articles from main collection
        all_data = self.main_db.collection.get(
            include=['documents', 'metadatas', 'embeddings']
        )
        
        total_articles = len(all_data['ids'])
        print(f"\nTotal articles in database: {total_articles}")
        
        # Track all entities (stocks + indices)
        all_entities = {**TOP_5_NIFTY, **INDICES}
        filtered_count = {company: 0 for company in all_entities.keys()}
        total_filtered = 0
        added_ids = set()  # Track added articles to avoid duplicates
        
        print("\nProcessing articles...")
        
        # Filter and copy relevant articles
        for i in range(total_articles):
            article_id = all_data['ids'][i]
            document = all_data['documents'][i]
            metadata = all_data['metadatas'][i]
            embedding = all_data['embeddings'][i]
            
            title = metadata.get('title', '')
            full_text = title + " " + document
            
            # Check each entity (stocks + indices)
            for company, company_data in all_entities.items():
                # Method 1: Direct keyword match (high confidence)
                if self.is_company_relevant(full_text, company_data['keywords']):
                    if article_id not in added_ids:
                        metadata['company'] = company
                        metadata['match_type'] = 'keyword'
                        
                        self.filtered_collection.add(
                            ids=[article_id],
                            documents=[document],
                            metadatas=[metadata],
                            embeddings=[embedding]
                        )
                        
                        added_ids.add(article_id)
                        filtered_count[company] += 1
                        total_filtered += 1
                        print(f"  ✓ [{company}] KEYWORD: {title[:50]}...")
                        break
        
        # Method 2: Semantic search for indirect impacts
        print("\nSearching for indirect impacts (government policies, sector news)...")
        
        for company, company_data in TOP_5_NIFTY.items():
            for query in company_data['semantic_queries']:
                # Use custom embedding for query to match database dimensions
                query_embedding = self.main_db._generate_embedding(query)
                
                results = self.main_db.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5  # Top 5 most relevant per query
                )
                
                if results['ids'] and len(results['ids'][0]) > 0:
                    for j in range(len(results['ids'][0])):
                        article_id = results['ids'][0][j]
                        similarity = 1 - results['distances'][0][j]
                        
                        # Only add if similarity is high enough and not already added
                        if similarity > 0.40 and article_id not in added_ids:
                            # Get the article data
                            idx = all_data['ids'].index(article_id)
                            document = all_data['documents'][idx]
                            metadata = all_data['metadatas'][idx].copy()
                            embedding = all_data['embeddings'][idx]
                            
                            metadata['company'] = company
                            metadata['match_type'] = 'semantic'
                            metadata['similarity'] = f"{similarity:.2%}"
                            metadata['matched_query'] = query
                            
                            self.filtered_collection.add(
                                ids=[article_id],
                                documents=[document],
                                metadatas=[metadata],
                                embeddings=[embedding]
                            )
                            
                            added_ids.add(article_id)
                            filtered_count[company] += 1
                            total_filtered += 1
                            print(f"  ✓ [{company}] SEMANTIC ({similarity:.0%}): {metadata['title'][:45]}...")
        
        print("\n" + "=" * 60)
        print("FILTERING COMPLETE")
        print("=" * 60)
        print(f"\nTotal filtered articles: {total_filtered}/{total_articles}")
        print("\nBy Company:")
        for company, count in filtered_count.items():
            print(f"  • {company}: {count}")
        
        return filtered_count
    
    def search_company_news(self, company: str, query: str = None, n_results: int = 10):
        """Search news for specific company"""
        if query:
            # Semantic search with company filter
            results = self.filtered_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"company": company}
            )
        else:
            # Get all articles for company
            results = self.filtered_collection.get(
                where={"company": company},
                limit=n_results
            )
        
        return results

def main():
    """Run the filtering"""
    filter_system = CompanyNewsFilter()
    filter_system.filter_and_copy()
    
    print("\n✓ Filtered database created!")
    print("\nYou can now search company-specific news:")
    print("  - Collection name: 'top10_nifty_news'")
    print("  - Stocks: Reliance, TCS, HDFC Bank, Infosys, ICICI Bank, Airtel, ITC, Wipro, HCL Tech, Bajaj Finance")
    print("  - Indices: NIFTY 50, SENSEX")

if __name__ == "__main__":
    main()
