# src/analyzers/sentiment.py
import google.generativeai as genai
from src.analyzers.models import RawItem, AnalyzedItem, FieldSentiment
from typing import List
import json
import os
from dotenv import load_dotenv

load_dotenv()


class SentimentAnalyzer:
    """
    Analyzes sentiment using Google Gemini with structured outputs.
    Performs field-level sentiment analysis for granular insights.
    """
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                'temperature': 0.1,  # Low for consistency
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            }
        )
    
    def analyze(self, item: RawItem) -> AnalyzedItem:
        """
        Analyze sentiment of a single item at field level.
        
        Args:
            item: RawItem to analyze
            
        Returns:
            AnalyzedItem with overall and field-level sentiments
        """
        
        entity = item.entity_mentioned[0]
        prompt = self._build_prompt(entity, item.text)
        
        try:
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise Exception("Empty response from Gemini")
            
            response_text = response.text
            result = self._parse_response(response_text)
            
            field_sentiments = [
                FieldSentiment(**fs) for fs in result["field_sentiments"]
            ]
            
            return AnalyzedItem(
                item_id=item.id,
                entity=entity,
                overall_sentiment=result["overall_sentiment"],
                field_sentiments=field_sentiments,
                timestamp=item.timestamp,
                platform=item.platform,
                raw_text=item.text
            )
            
        except Exception as e:
            raise Exception(f"Failed to analyze sentiment: {str(e)}")
    
    def _build_prompt(self, entity: str, text: str) -> str:
        """Build analysis prompt"""
        
        prompt = f"""You are a sentiment analysis expert. Analyze the sentiment about {entity} in this text.

TEXT TO ANALYZE:
{text}

TASK:
Extract sentiment for these specific fields (ONLY if mentioned):
- ad_quality: Quality, intrusiveness of ads
- user_experience: Interface, usability
- revenue_potential: Monetization, earnings
- customer_support: Support quality
- performance: Speed, reliability
- brand_reputation: Brand perception

For EACH field mentioned, provide:
1. sentiment: "positive", "negative", "neutral", or "mixed"
2. confidence: 0.0 to 1.0
3. quote: exact text snippet (max 50 words)
4. reasoning: brief explanation (1 sentence)

Also provide overall_sentiment.

CRITICAL: Output MUST be valid JSON only, no markdown, no other text.

OUTPUT FORMAT:
{{
  "overall_sentiment": "positive",
  "field_sentiments": [
    {{
      "field": "ad_quality",
      "sentiment": "negative",
      "confidence": 0.85,
      "quote": "exact quote",
      "reasoning": "explanation"
    }}
  ]
}}

Respond with ONLY the JSON."""

        return prompt
    
    def _parse_response(self, response_text: str) -> dict:
        """Parse JSON from response"""
        
        # Remove markdown if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith('{'):
                    response_text = part
                    break
        
        response_text = response_text.strip()
        
        try:
            result = json.loads(response_text)
            
            # Validate
            if "overall_sentiment" not in result:
                raise ValueError("Missing overall_sentiment")
            if "field_sentiments" not in result:
                result["field_sentiments"] = []
            
            valid_sentiments = ["positive", "negative", "neutral", "mixed"]
            if result["overall_sentiment"] not in valid_sentiments:
                result["overall_sentiment"] = "neutral"
            
            for fs in result["field_sentiments"]:
                if "sentiment" not in fs or fs["sentiment"] not in valid_sentiments:
                    fs["sentiment"] = "neutral"
                if "confidence" not in fs or not (0.0 <= fs["confidence"] <= 1.0):
                    fs["confidence"] = 0.5
                if "quote" not in fs:
                    fs["quote"] = "N/A"
                if "reasoning" not in fs:
                    fs["reasoning"] = "N/A"
                if "field" not in fs:
                    fs["field"] = "unknown"
            
            return result
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON: {e}\nResponse: {response_text[:500]}")


# Test
if __name__ == "__main__":
    from datetime import datetime
    
    test_item = RawItem(
        id="test_1",
        platform="google_search",
        entity_mentioned=["Taboola"],
        text="Taboola ads are everywhere and quite intrusive, but they pay publishers really well. The CPM is solid.",
        author="test_user",
        timestamp=datetime.now(),
        url="https://example.com/test"
    )
    
    print("🧪 Testing Gemini Sentiment Analyzer...\n")
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze(test_item)
    
    print(f"✅ Analysis complete!")
    print(f"Overall: {result.overall_sentiment}")
    print(f"\nField sentiments:")
    for fs in result.field_sentiments:
        print(f"  - {fs.field}: {fs.sentiment} (confidence: {fs.confidence:.2f})")
        print(f"    Quote: '{fs.quote}'")
        print(f"    Reasoning: {fs.reasoning}\n")
