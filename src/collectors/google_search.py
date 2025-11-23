# src/collectors/google_search.py
from src.collectors.base import BaseCollector
from typing import List
from src.analyzers.models import RawItem
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv


load_dotenv()


class GoogleSearchCollector(BaseCollector):
    """Collects results from Google Search using SerpAPI"""
    
    def __init__(self, days_back: int = 30):
        """
        Args:
            days_back: How many days back to search (default 30)
        """
        self.api_key = os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search"
        self.days_back = days_back
    
    def collect(self, keywords: List[str], limit: int = 50) -> List[RawItem]:
        """Collect items from Google Search"""
        items = []
        seen_urls = set()
        
        # ✅ Calculate date filter
        start_date = (datetime.now() - timedelta(days=self.days_back)).strftime('%Y-%m-%d')
        
        for keyword in keywords:
            queries = [
                f'"{keyword}" review after:{start_date}',
                f'"{keyword}" opinion site:reddit.com OR site:news.ycombinator.com after:{start_date}',
                f'"{keyword}" experience after:{start_date}'
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
                        url = result.get('link', '')
                        
                        if url in seen_urls:
                            continue
                        
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
                        
                        seen_urls.add(url)
                        
                        item = RawItem(
                            id=f"google_{abs(hash(url))}",
                            platform="google_search",
                            entity_mentioned=entities,
                            text=text,
                            author=result.get('source', 'unknown'),
                            timestamp=datetime.now(),
                            url=url
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
    # ✅ Test with different time ranges
    collector = GoogleSearchCollector(days_back=7)  # Last week
    items = collector.collect(keywords=["Taboola"], limit=20)
    print(f"✅ Collected {len(items)} items from the last 7 days")
    for item in items[:3]:
        print(f"\n📄 {item.url}")
        print(f"   {item.text[:80]}...")
