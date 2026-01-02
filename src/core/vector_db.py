import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import hashlib
import requests
from src.utils.config import config

class VectorDB:
    """Vector database for storing and searching news articles"""
    
    def __init__(self):
        """Initialize ChromaDB and Jina AI API"""
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Check Jina API key
        if not config.JINA_API_KEY:
            print("WARNING: JINA_API_KEY not set. Embeddings will not work.")
            print("   Get your free API key at: https://jina.ai/")
        else:
            print(f"Using Jina AI API: {config.JINA_MODEL}")
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=config.COLLECTION_NAME,
            metadata={"description": "Economic news articles with embeddings"}
        )
        print(f"Connected to collection: {config.COLLECTION_NAME}")
    
    def _generate_id(self, url: str) -> str:
        """Generate unique ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_retry_session(self, retries=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504]):
        """Create a requests session with retry logic"""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        session = requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Jina AI API (with retry)"""
        if not config.JINA_API_KEY:
            raise ValueError("JINA_API_KEY not configured")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.JINA_API_KEY}"
        }
        
        data = {
            "model": config.JINA_MODEL,
            "input": [text]
        }
        
        try:
            session = self._get_retry_session()
            response = session.post(
                config.JINA_API_URL,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result['data'][0]['embedding']
        except Exception as e:
            print(f"Error generating embedding (after retries): {e}")
            raise
    
    def article_exists(self, url: str) -> bool:
        """Check if article already exists in database"""
        article_id = self._generate_id(url)
        try:
            result = self.collection.get(ids=[article_id])
            return len(result['ids']) > 0
        except:
            return False
    
    def add_article(
        self, 
        title: str, 
        description: str, 
        url: str, 
        source: str,
        published_date: str,
        category: str = ""
    ) -> bool:
        """Add article to vector database"""
        
        # Check if already exists
        if self.article_exists(url):
            print(f"  Skipping duplicate: {title[:60]}...")
            return False
        
        # Generate ID
        article_id = self._generate_id(url)
        
        # Combine title and description for embedding
        text_to_embed = f"{title}\n\n{description}"
        
        # Generate embedding
        embedding = self._generate_embedding(text_to_embed)
        
        # Prepare metadata
        metadata = {
            "title": title,
            "source": source,
            "url": url,
            "published_date": published_date,
            "category": category
        }
        
        # Add to collection
        self.collection.add(
            ids=[article_id],
            embeddings=[embedding],
            documents=[text_to_embed],
            metadatas=[metadata]
        )
        
        print(f"  Added: {title[:60]}...")
        return True
    
    def search(self, query: str, n_results: int = 10) -> List[Dict]:
        """Search for articles semantically similar to query"""
        
        # Generate query embedding
        query_embedding = self._generate_embedding(query)
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        articles = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                article = {
                    'id': results['ids'][0][i],
                    'title': results['metadatas'][0][i]['title'],
                    'source': results['metadatas'][0][i]['source'],
                    'url': results['metadatas'][0][i]['url'],
                    'published_date': results['metadatas'][0][i]['published_date'],
                    'category': results['metadatas'][0][i].get('category', ''),
                    'distance': results['distances'][0][i] if 'distances' in results else None,
                    'snippet': results['documents'][0][i][:200] + "..."
                }
                articles.append(article)
        
        return articles
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        count = self.collection.count()
        
        # Get all metadata to count by source
        if count > 0:
            all_data = self.collection.get()
            sources = {}
            for metadata in all_data['metadatas']:
                source = metadata['source']
                sources[source] = sources.get(source, 0) + 1
            
            return {
                'total_articles': count,
                'by_source': sources
            }
        
        return {
            'total_articles': 0,
            'by_source': {}
        }
    
    def clear_all(self):
        """Clear all data from collection"""
        self.client.delete_collection(config.COLLECTION_NAME)
        self.collection = self.client.create_collection(
            name=config.COLLECTION_NAME,
            metadata={"description": "Economic news articles with embeddings"}
        )
        print("All data cleared")

if __name__ == "__main__":
    # Test the vector database
    db = VectorDB()
    print(f"\nDatabase stats: {db.get_stats()}")
