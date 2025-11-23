# src/analyzers/llm_analyzer.py
import os
import json
import time
from typing import List, Optional
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai
from src.analyzers.models import RawItem, AnalyzedItem
from datetime import datetime

project_root = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=project_root / ".env")


class AnalysisResult(BaseModel):
    sentiment: str = Field(..., description="positive, neutral, or negative")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Score from -1 to 1")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Star rating if mentioned")
    topics: List[str] = Field(default_factory=list, description="List of topics mentioned")
    category: str = Field(..., description="complaint, review, question, praise, or feature_request")
    key_insight: str = Field(..., max_length=200, description="One sentence core message")
    summary: str = Field(..., max_length=100, description="Professional summary for dashboard")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in analysis")
    actionable: bool = Field(..., description="Requires response or action")
    response_draft: Optional[str] = Field(None, description="Draft reply if actionable")



class LLMAnalyzer:
    """Analyzes raw items using Gemini LLM"""
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        """
        Initialize LLM Analyzer with Gemini
        
        Args:
            model: Model to use
                - gemini-2.5-flash (recommended - fast & cheap)
                - gemini-2.5-flash-exp (more capable but slower)
                - gemini-2.5-flash-exp (experimental, might be unstable)
        """

        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ GEMINI_API_KEY not found in .env")
        
        genai.configure(api_key=self.api_key)
        self.model = self._init_model_with_fallbacks(model)

    def _init_model_with_fallbacks(self, requested: str):
        """Try a set of compatible Gemini model IDs until one works for generate_content."""
        candidates = [
            requested,
            "gemini-2.5-flash-exp",
            "gemini-2.5-flash",
            "gemini-2.5-flash-8b",
            "gemini-2.5-pro-exp",
            "gemini-2.5-pro",
        ]
        last_err = None
        for m in candidates:
            try:
                mdl = genai.GenerativeModel(
                    model_name=m,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.8,
                        "top_k": 40,
                        "max_output_tokens": 2048,
                    },
                )
                # Warm-up minimal call to verify availability
                _ = mdl.generate_content("ping")
                return mdl
            except Exception as e:
                last_err = e
                continue
        # If none worked, raise the last error
        raise RuntimeError(f"No supported Gemini model available. Last error: {last_err}")
    
    def analyze(self, items: List[RawItem], delay: float = 7.0) -> List[AnalyzedItem]:
        """
        Analyze multiple items with rate limiting
        
        Args:
            items: List of raw items to analyze
            delay: Delay between requests in seconds (default 7s)
            
        Returns:
            List of analyzed items with LLM insights
        """
        analyzed_items = []
        
        for i, item in enumerate(items, 1):
            try:
                analyzed = self._analyze_single(item)
                analyzed_items.append(analyzed)
                print(f"✅ Analyzed {i}/{len(items)}: {item.id}")
                
                # Rate limiting: wait between requests
                if i < len(items):  # Don't wait after last item
                    print(f"⏳ Waiting {delay}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"❌ Error analyzing {item.id}: {str(e)[:100]}")
                # Fallback to basic analysis
                analyzed_items.append(self._fallback_analysis(item))
        
        return analyzed_items
    
    def _analyze_single(self, item: RawItem) -> AnalyzedItem:
        """Analyze a single item using Gemini with Pydantic validation and retry"""

        prompt = self._build_prompt(item)

        # Try up to 2 attempts: first with base prompt, then with schema-reminder
        attempts = 2
        last_err: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            p = prompt if attempt == 1 else (
                prompt
                + "\n\nReturn ONLY valid compact JSON matching this schema strictly: "
                + "{sentiment, sentiment_score, rating, topics, category, key_insight, summary, confidence, actionable, response_draft}."
            )

            # Call Gemini API
            response = self.model.generate_content(p)

            # Extract JSON from response (handle markdown code blocks if present)
            response_text = (getattr(response, "text", "") or "").strip()

            if "```json" in response_text:
                try:
                    response_text = response_text.split("```json", 1)[1].split("```", 1)[0].strip()
                except Exception:
                    response_text = response_text
            elif "```" in response_text:
                parts = response_text.split("```")
                for part in parts:
                    ptxt = part.strip()
                    if ptxt.startswith('{'):
                        response_text = ptxt
                        break
            response_text = response_text.strip()

            try:
                raw = json.loads(response_text)
                validated = AnalysisResult(**raw)
                return self._to_analyzed_item(item, validated)
            except (json.JSONDecodeError, ValidationError) as e:
                last_err = e
                continue

        # If validation failed after retries, raise to trigger fallback
        raise Exception(f"Validation failed: {str(last_err)[:200]}")

    def _to_analyzed_item(self, item: RawItem, vr: AnalysisResult) -> AnalyzedItem:
        return AnalyzedItem(
            id=item.id,
            text=item.text,
            url=str(item.url),
            timestamp=item.timestamp,
            platform=item.platform,
            entity_mentioned=item.entity_mentioned,
            author=item.author,
            sentiment=vr.sentiment,
            sentiment_score=vr.sentiment_score,
            rating=vr.rating,
            topics=vr.topics,
            category=vr.category,
            key_insight=vr.key_insight,
            summary=vr.summary,
            confidence=vr.confidence,
            actionable=vr.actionable,
            response_status="pending" if vr.actionable else "ignored",
            response_draft=vr.response_draft,
            assigned_to=None,
        )
    
    def _build_prompt(self, item: RawItem) -> str:
        """Build analysis prompt for Gemini"""
        
        entities_str = ", ".join(item.entity_mentioned)
        
        prompt = f"""Analyze this user feedback about {entities_str}:

**Text:** {item.text}

**Source:** {item.platform}
**URL:** {item.url}
**Author:** {item.author}

Provide a structured analysis in JSON format with these fields:

1. **sentiment**: "positive", "neutral", or "negative"
2. **sentiment_score**: Float from -1.0 (very negative) to +1.0 (very positive)
3. **rating**: Integer 1-5 stars if explicitly mentioned in text, otherwise null
4. **category**: One of: "complaint", "review", "question", "praise", "feature_request"
5. **topics**: List of relevant topics (e.g., ["pricing", "ad_quality", "support", "integration"])
6. **key_insight**: One sentence capturing the core message (max 20 words)
7. **summary**: Professional 10-15 word summary suitable for dashboard
8. **confidence**: Float 0.0-1.0 indicating your confidence in this analysis
9. **actionable**: Boolean - true if this requires a response or action from the company
10. **response_draft**: If actionable=true, generate a professional, empathetic reply draft (2-3 sentences). Otherwise null.

**Important guidelines:**
- Be objective and professional
- Extract actual topics mentioned (don't invent topics not in text)
- For rating: only include if user explicitly mentions stars/rating (e.g., "3/5", "4 stars")
- Response draft should be empathetic, acknowledge the issue, and suggest next steps
- Response should be personalized to the specific feedback

Return ONLY valid JSON, no markdown formatting or explanations.

Example output:
{{
  "sentiment": "negative",
  "sentiment_score": -0.6,
  "rating": 2,
  "category": "complaint",
  "topics": ["pricing", "ad_quality"],
  "key_insight": "User frustrated with high CPM and intrusive ad placements",
  "summary": "Negative feedback on pricing and ad quality from publisher",
  "confidence": 0.85,
  "actionable": true,
  "response_draft": "Thank you for sharing your feedback. We understand your concerns about pricing and ad quality. Our team would love to discuss optimization strategies tailored to your site. Can we schedule a call this week?"
}}
"""
        return prompt
    
    def _fallback_analysis(self, item: RawItem) -> AnalyzedItem:
        """Fallback analysis if LLM fails"""
        
        text_lower = item.text.lower()
        
        # Simple sentiment detection
        negative_words = ["bad", "terrible", "awful", "hate", "worst", "poor", "disappointing"]
        positive_words = ["good", "great", "excellent", "love", "best", "amazing", "fantastic"]
        
        neg_count = sum(1 for word in negative_words if word in text_lower)
        pos_count = sum(1 for word in positive_words if word in text_lower)
        
        if neg_count > pos_count:
            sentiment = "negative"
            score = -0.5
        elif pos_count > neg_count:
            sentiment = "positive"
            score = 0.5
        else:
            sentiment = "neutral"
            score = 0.0
        
        return AnalyzedItem(
            id=item.id,
            text=item.text,
            url=str(item.url),  # ⬅️ Convert to string
            timestamp=item.timestamp,
            platform=item.platform,
            entity_mentioned=item.entity_mentioned,
            author=item.author,
            sentiment=sentiment,
            sentiment_score=score,
            rating=None,
            topics=["general"],
            category="review",
            key_insight="Unable to analyze - LLM error",
            summary="Analysis unavailable",
            confidence=0.3,
            actionable=False,
            response_status="ignored",
            response_draft=None,
            assigned_to=None
        )


# Test
if __name__ == "__main__":
    from src.collectors.google_search import GoogleSearchCollector
    
    # Collect some items
    print("🔍 Collecting items...")
    collector = GoogleSearchCollector(days_back=7)
    raw_items = collector.collect(keywords=["Taboola"], limit=5)
    print(f"✅ Collected {len(raw_items)} items\n")
    
    # Analyze items
    print("🧠 Analyzing items with Gemini...")
    analyzer = LLMAnalyzer()
    analyzed_items = analyzer.analyze(raw_items, delay=7.0)
    print(f"✅ Analyzed {len(analyzed_items)} items\n")
    
    # Print results
    for item in analyzed_items:
        print(f"\n{'='*60}")
        print(f"📄 {item.url}")
        print(f"😊 Sentiment: {item.sentiment} ({item.sentiment_score:.2f})")
        if item.rating:
            print(f"⭐ Rating: {item.rating}/5")
        print(f"📂 Category: {item.category}")
        print(f"🏷️  Topics: {', '.join(item.topics)}")
        print(f"💡 Insight: {item.key_insight}")
        print(f"📝 Summary: {item.summary}")
        if item.response_draft:
            print(f"💬 Draft Reply: {item.response_draft}")
        print(f"✅ Actionable: {item.actionable}")
