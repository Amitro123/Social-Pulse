# src/aggregators/stats_aggregator.py
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta
from src.analyzers.models import AnalyzedItem, AggregatedStats


class StatsAggregator:
    """Aggregates analyzed items into statistics and insights"""
    
    def aggregate(
        self, 
        items: List[AnalyzedItem],
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Aggregate analyzed items into stats
        
        Args:
            items: List of analyzed items
            days_back: Number of days for date range
            
        Returns:
            Dictionary with aggregated stats
        """
        if not items:
            return self._empty_stats(days_back)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Sentiment breakdown
        sentiment_counts = Counter([item.sentiment for item in items])
        
        # Average sentiment score
        avg_sentiment = sum([item.sentiment_score for item in items]) / len(items)
        
        # Average rating (only items with ratings)
        items_with_rating = [item for item in items if item.rating is not None]
        avg_rating = (
            sum([item.rating for item in items_with_rating]) / len(items_with_rating)
            if items_with_rating else None
        )
        
        # Sentiment trend (group by day)
        sentiment_trend = self._calculate_sentiment_trend(items)
        
        # Hot topics
        hot_topics = self._calculate_hot_topics(items)
        
        # Action required count
        action_required = [item for item in items if item.actionable]
        
        # Response stats
        response_stats = self._calculate_response_stats(items)
        
        # Build stats object
        stats = {
            "total_mentions": len(items),
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "sentiment_breakdown": {
                "positive": sentiment_counts.get("positive", 0),
                "neutral": sentiment_counts.get("neutral", 0),
                "negative": sentiment_counts.get("negative", 0)
            },
            "sentiment_percentages": {
                "positive": round(sentiment_counts.get("positive", 0) / len(items) * 100, 1),
                "neutral": round(sentiment_counts.get("neutral", 0) / len(items) * 100, 1),
                "negative": round(sentiment_counts.get("negative", 0) / len(items) * 100, 1)
            },
            "average_sentiment_score": round(avg_sentiment, 2),
            "average_rating": round(avg_rating, 1) if avg_rating else None,
            "sentiment_trend": sentiment_trend,
            "hot_topics": hot_topics,
            "action_required_count": len(action_required),
            "action_required_items": [
                {
                    "id": item.id,
                    "sentiment": item.sentiment,
                    "category": item.category,
                    "topics": item.topics,
                    "key_insight": item.key_insight,
                    "url": item.url
                }
                for item in action_required[:10]  # Top 10
            ],
            "response_stats": response_stats,
            "category_breakdown": self._calculate_category_breakdown(items),
            "platform_breakdown": self._calculate_platform_breakdown(items)
        }
        
        return stats
    
    def _calculate_sentiment_trend(self, items: List[AnalyzedItem]) -> List[Dict[str, Any]]:
        """Calculate sentiment trend over time"""
        
        # Group by date
        items_by_date = {}
        for item in items:
            date_key = item.timestamp.date().isoformat()
            if date_key not in items_by_date:
                items_by_date[date_key] = []
            items_by_date[date_key].append(item)
        
        # Calculate average sentiment per day
        trend = []
        for date_key, date_items in sorted(items_by_date.items()):
            avg_score = sum([i.sentiment_score for i in date_items]) / len(date_items)
            trend.append({
                "date": date_key,
                "score": round(avg_score, 2),
                "count": len(date_items)
            })
        
        return trend
    
    def _calculate_hot_topics(self, items: List[AnalyzedItem]) -> List[Dict[str, Any]]:
        """Calculate most mentioned topics with sentiment"""
        
        topic_data = {}
        
        for item in items:
            for topic in item.topics:
                if topic not in topic_data:
                    topic_data[topic] = {
                        "count": 0,
                        "sentiment_scores": []
                    }
                topic_data[topic]["count"] += 1
                topic_data[topic]["sentiment_scores"].append(item.sentiment_score)
        
        # Calculate average sentiment per topic
        hot_topics = []
        for topic, data in topic_data.items():
            avg_sentiment = sum(data["sentiment_scores"]) / len(data["sentiment_scores"])
            hot_topics.append({
                "topic": topic,
                "count": data["count"],
                "avg_sentiment": round(avg_sentiment, 2)
            })
        
        # Sort by count (descending)
        hot_topics.sort(key=lambda x: x["count"], reverse=True)
        
        return hot_topics[:10]  # Top 10
    
    def _calculate_response_stats(self, items: List[AnalyzedItem]) -> Dict[str, int]:
        """Calculate response statistics"""
        
        status_counts = Counter([item.response_status for item in items])
        
        return {
            "pending": status_counts.get("pending", 0),
            "replied": status_counts.get("replied", 0),
            "in_campaign": status_counts.get("in_campaign", 0),
            "ignored": status_counts.get("ignored", 0)
        }
    
    def _calculate_category_breakdown(self, items: List[AnalyzedItem]) -> Dict[str, int]:
        """Calculate breakdown by category"""
        
        category_counts = Counter([item.category for item in items])
        
        return dict(category_counts)
    
    def _calculate_platform_breakdown(self, items: List[AnalyzedItem]) -> Dict[str, int]:
        """Calculate breakdown by platform"""
        
        platform_counts = Counter([item.platform for item in items])
        
        return dict(platform_counts)
    
    def _empty_stats(self, days_back: int) -> Dict[str, Any]:
        """Return empty stats structure"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return {
            "total_mentions": 0,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "sentiment_breakdown": {"positive": 0, "neutral": 0, "negative": 0},
            "sentiment_percentages": {"positive": 0, "neutral": 0, "negative": 0},
            "average_sentiment_score": 0.0,
            "average_rating": None,
            "sentiment_trend": [],
            "hot_topics": [],
            "action_required_count": 0,
            "action_required_items": [],
            "response_stats": {"pending": 0, "replied": 0, "in_campaign": 0, "ignored": 0},
            "category_breakdown": {},
            "platform_breakdown": {}
        }


if __name__ == "__main__":
    from src.collectors.google_search import GoogleSearchCollector
    from src.analyzers.llm_analyzer import LLMAnalyzer
    import json
    
    # Collect items
    print("🔍 Collecting items...")
    collector = GoogleSearchCollector(days_back=30)
    raw_items = collector.collect(keywords=["Taboola"], limit=10)  # ⬅️ Reduced to 10
    print(f"✅ Collected {len(raw_items)} items\n")
    
    # Analyze items
    print("🧠 Analyzing items...")
    analyzer = LLMAnalyzer()
    analyzed_items = analyzer.analyze(raw_items, delay=6.5)  # ⬅️ 6.5s delay
    print(f"✅ Analyzed {len(analyzed_items)} items\n")
    
    # Aggregate stats
    print("📊 Aggregating statistics...")
    aggregator = StatsAggregator()
    stats = aggregator.aggregate(analyzed_items, days_back=30)
    print(f"✅ Aggregated stats\n")
    
    # Print stats - FIX JSON serialization
    print("="*60)
    print("📊 AGGREGATED STATISTICS")
    print("="*60)
    
    # Convert datetime and other non-serializable objects
    def serialize_stats(obj):
        """Custom JSON serializer"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
    
    print(json.dumps(stats, indent=2, ensure_ascii=False, default=serialize_stats))
