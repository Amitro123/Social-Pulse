# src/main.py
import argparse
import sys
import json
from pathlib import Path
from typing import List

from src.utils.logger import setup_logger
from src.utils.config import load_config
from src.collectors.google_search import GoogleSearchCollector
from src.analyzers.sentiment import SentimentAnalyzer
from src.analyzers.models import RawItem, AnalyzedItem

logger = setup_logger(__name__)


def collect_data(config: dict, limit: int = 30) -> List[RawItem]:
    """Collect data from Google Search"""
    logger.info("🔍 Starting data collection from Google Search...")
    
    keywords = config.get('keywords', ['Taboola', 'Realize'])
    
    try:
        collector = GoogleSearchCollector()
        items = collector.collect(keywords=keywords, limit=limit)
        
        logger.info(f"✅ Collected {len(items)} items")
        
        # Save raw items
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "items.json", "w", encoding="utf-8") as f:
            json.dump(
                [item.model_dump(mode="json") for item in items],
                f,
                indent=2,
                default=str
            )
        logger.info(f"💾 Saved raw items to outputs/items.json")
        
        return items
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


def analyze_sentiment(items: List[RawItem], config: dict, limit: int = 15) -> List[AnalyzedItem]:
    """Analyze sentiment of collected items"""
    logger.info(f"🧠 Starting sentiment analysis on {len(items)} items...")
    
    analyzer = SentimentAnalyzer()
    analyzed_items: List[AnalyzedItem] = []
    
    # Limit to avoid excessive API costs
    items_to_analyze = items[:limit]
    
    for i, item in enumerate(items_to_analyze, 1):
        logger.info(f"  Analyzing {i}/{len(items_to_analyze)}: {item.id}")
        
        try:
            analyzed = analyzer.analyze(item)
            analyzed_items.append(analyzed)
            
            # Log summary
            logger.info(f"    Overall: {analyzed.overall_sentiment}, "
                       f"Fields: {len(analyzed.field_sentiments)}")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to analyze {item.id}: {e}")
            continue
    
    logger.info(f"✅ Successfully analyzed {len(analyzed_items)} items")
    
    # Save analyzed items
    output_dir = Path("outputs")
    with open(output_dir / "analyzed.json", "w", encoding="utf-8") as f:
        json.dump(
            [item.model_dump(mode="json") for item in analyzed_items],
            f,
            indent=2,
            default=str
        )
    logger.info(f"💾 Saved analyzed items to outputs/analyzed.json")
    
    return analyzed_items


def generate_report(analyzed_items: List[AnalyzedItem]):
    """Generate summary report"""
    logger.info("📊 Generating summary report...")
    
    if not analyzed_items:
        logger.warning("No analyzed items to report on")
        return
    
    # Calculate statistics
    sentiment_counts = {
        'positive': 0,
        'negative': 0,
        'neutral': 0,
        'mixed': 0
    }
    
    field_sentiments = {}
    
    for item in analyzed_items:
        sentiment_counts[item.overall_sentiment] += 1
        
        for fs in item.field_sentiments:
            if fs.field not in field_sentiments:
                field_sentiments[fs.field] = {
                    'positive': 0,
                    'negative': 0,
                    'neutral': 0,
                    'mixed': 0
                }
            field_sentiments[fs.field][fs.sentiment] += 1
    
    # Generate markdown report
    report_lines = [
        "# Social Pulse - Sentiment Analysis Report\n",
        f"**Total Items Analyzed:** {len(analyzed_items)}\n",
        "\n## Overall Sentiment Distribution\n",
        f"- Positive: {sentiment_counts['positive']} ({sentiment_counts['positive']/len(analyzed_items)*100:.1f}%)",
        f"- Negative: {sentiment_counts['negative']} ({sentiment_counts['negative']/len(analyzed_items)*100:.1f}%)",
        f"- Neutral: {sentiment_counts['neutral']} ({sentiment_counts['neutral']/len(analyzed_items)*100:.1f}%)",
        f"- Mixed: {sentiment_counts['mixed']} ({sentiment_counts['mixed']/len(analyzed_items)*100:.1f}%)",
        "\n## Field-Level Sentiment Breakdown\n"
    ]
    
    for field, counts in field_sentiments.items():
        total = sum(counts.values())
        report_lines.append(f"\n### {field.replace('_', ' ').title()}")
        report_lines.append(f"- Positive: {counts['positive']} ({counts['positive']/total*100:.1f}%)")
        report_lines.append(f"- Negative: {counts['negative']} ({counts['negative']/total*100:.1f}%)")
        report_lines.append(f"- Neutral: {counts['neutral']} ({counts['neutral']/total*100:.1f}%)")
    
    report_text = "\n".join(report_lines)
    
    # Save report
    output_dir = Path("outputs")
    with open(output_dir / "report.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    
    logger.info(f"💾 Saved report to outputs/report.md")
    
    # Print summary to console
    print("\n" + "="*60)
    print("📊 SENTIMENT ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total Items: {len(analyzed_items)}")
    print(f"\nOverall Sentiment:")
    for sentiment, count in sentiment_counts.items():
        percentage = count/len(analyzed_items)*100
        print(f"  {sentiment.title()}: {count} ({percentage:.1f}%)")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Social Pulse - AI-powered sentiment analysis tool for brand monitoring"
    )
    parser.add_argument(
        "--collect", 
        action="store_true", 
        help="Collect data from Google Search"
    )
    parser.add_argument(
        "--analyze", 
        action="store_true", 
        help="Analyze sentiment of collected data"
    )
    parser.add_argument(
        "--report", 
        action="store_true", 
        help="Generate summary report"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run complete pipeline (collect -> analyze -> report)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=30, 
        help="Limit number of items to collect (default: 30)"
    )
    parser.add_argument(
        "--analyze-limit", 
        type=int, 
        default=15, 
        help="Limit number of items to analyze (default: 15, to manage API costs)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # If no action specified, print help
    if not any([args.collect, args.analyze, args.report, args.all]):
        parser.print_help()
        sys.exit(1)
    
    try:
        logger.info("🚀 Social Pulse - Starting...")
        
        raw_items = []
        analyzed_items = []
        
        # Complete pipeline
        if args.all:
            # 1. Collect
            raw_items = collect_data(config, limit=args.limit)
            
            # 2. Analyze
            analyzed_items = analyze_sentiment(raw_items, config, limit=args.analyze_limit)
            
            # 3. Report
            generate_report(analyzed_items)
        
        # Individual steps
        else:
            if args.collect:
                raw_items = collect_data(config, limit=args.limit)
            
            if args.analyze:
                # Load items if not already collected
                if not raw_items:
                    logger.info("Loading items from outputs/items.json...")
                    with open("outputs/items.json", "r", encoding="utf-8") as f:
                        items_data = json.load(f)
                        raw_items = [RawItem(**item) for item in items_data]
                
                analyzed_items = analyze_sentiment(raw_items, config, limit=args.analyze_limit)
            
            if args.report:
                # Load analyzed items if not already analyzed
                if not analyzed_items:
                    logger.info("Loading analyzed items from outputs/analyzed.json...")
                    with open("outputs/analyzed.json", "r", encoding="utf-8") as f:
                        analyzed_data = json.load(f)
                        analyzed_items = [AnalyzedItem(**item) for item in analyzed_data]
                
                generate_report(analyzed_items)
        
        logger.info("✅ Done! Check outputs/ folder for results")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
