# src/collectors/google_search.py
from src.collectors.base import BaseCollector
from typing import List
from src.analyzers.models import RawItem
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleSearchCollector(BaseCollector):
    """Collects results from Google Search using SerpAPI"""
    
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search"
    
    def collect(self, keywords: List[str], limit: int = 50) -> List[RawItem]:
        """Collect items from Google Search"""
        items = []
        
        for keyword in keywords:
            queries = [
                f'"{keyword}" review',
                f'"{keyword}" opinion site:reddit.com OR site:news.ycombinator.com',
                f'"{keyword}" experience'
            ]
            
            for query in queries:
                if len(items) >= limit:
                    break
                    
                params = {
                    'q': query,
                    'api_key': self.api_key,
                    'num': 10,
                    'hl': 'en'
                }
                
                try:
                    response = requests.get(self.base_url, params=params)
                    data = response.json()
                    
                    for result in data.get('organic_results', []):
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        text = f"{title}\n{snippet}"
                        
                        # Detect entities
                        entities = []
                        text_lower = text.lower()
                        if 'taboola' in text_lower:
                            entities.append('Taboola')
                        if 'realize' in text_lower:
                            entities.append('Realize')
                        
                        if not entities:
                            continue
                        
                        item = RawItem(
                            id=f"google_{abs(hash(result['link']))}",
                            platform="google_search",
                            entity_mentioned=entities,
                            text=text,
                            author=result.get('source', 'unknown'),
                            timestamp=datetime.now(),
                            url=result['link']
                        )
                        items.append(item)
                        
                        if len(items) >= limit:
                            return items
                
                except Exception as e:
                    print(f"❌ Error searching '{query}': {e}")
                    continue
        
        return items

# Test
if __name__ == "__main__":
    collector = GoogleSearchCollector()
    items = collector.collect(keywords=["Taboola"], limit=20)
    print(f"✅ Collected {len(items)} items")
    for item in items[:3]:
        print(f"\n📄 {item.url}")
        print(f"   {item.text[:80]}...")
