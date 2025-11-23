# Social Pulse - Agent Architecture & Planning

**Project Name:** social-pulse  
**Purpose:** Mini Social Listening Agent for Taboola Take-Home Assignment  
**Target:** AI Implementation Engineer Role

---

## 🎯 Project Goal


## 🏗️ System Architecture

### High-Level Flow
┌─────────────┐ ┌───────────┐ ┌──────────┐ ┌────────────┐ ┌─────┐
│ Data Sources│ -> │Collectors │ -> │ Analyzer │ -> │ Aggregator │ -> │ UI │
│ Reddit/LI │ │ (PRAW) │ │ (LLM) │ │ (Stats) │ │React│
└─────────────┘ └───────────┘ └──────────┘ └────────────┘ └─────┘

### Component Breakdown

#### 1. **Data Collection Layer** (`src/collectors/`)

**Purpose:** Fetch and normalize data from multiple sources

**Components:**
- `BaseCollector` (abstract): Common interface for all collectors
- `RedditCollector`: Uses PRAW to search Reddit
- `LinkedInCollector`: Scrapes public LinkedIn posts (bonus)

**Output Format:**
{
"id": "reddit_abc123",
"platform": "reddit",
"entity_mentioned": ["Taboola"],
"text": "Taboola ads are everywhere but they pay well...",
"author": "user123",
"timestamp": "2025-11-23T10:00:00Z",
"url": "https://reddit.com/r/webdev/comments/abc123"
}


**Key Features:**
- Rate limit handling
- Deduplication
- Error recovery
- Progress tracking

---

#### 2. **Sentiment Analysis Layer** (`src/analyzers/`)

**Purpose:** Extract field-level sentiment using LLM

**Components:**
- `SentimentAnalyzer`: Main LLM integration
- `PromptBuilder`: Constructs optimal prompts
- `SchemaValidator`: Ensures output consistency

**Critical Design Choice: Field-Level Analysis**

Instead of just "positive/negative", we analyze specific aspects:
- `ad_quality`: Quality and intrusiveness of ads
- `user_experience`: Interface and usability
- `revenue_potential`: Monetization effectiveness
- `customer_support`: Support quality
- `performance`: Speed and reliability
- `brand_reputation`: Overall brand perception

**Output Format:**
{
"item_id": "reddit_abc123",
"entity": "Taboola",
"overall_sentiment": "mixed",
"field_sentiments": [
{
"field": "ad_quality",
"sentiment": "negative",
"confidence": 0.85,
"quote": "ads are everywhere",
"reasoning": "User expresses frustration with ad prevalence"
},
{
"field": "revenue_potential",
"sentiment": "positive",
"confidence": 0.90,
"quote": "they pay well",
"reasoning": "Indicates good monetization for publishers"
}
],
"timestamp": "2025-11-23T10:00:00Z",
"platform": "reddit"
}

**Prompt Strategy:**
- Short, explicit instructions
- JSON Schema enforcement via `response_format`
- Few-shot examples for edge cases
- Explicit handling of sarcasm, mixed sentiment, ambiguity

---

#### 3. **Aggregation Layer** (`src/aggregators/`)

**Purpose:** Transform individual analyses into actionable insights

**Components:**
- `StatisticsAggregator`: Calculate distributions and percentages
- `ThemeExtractor`: Identify recurring topics using LLM or clustering
- `TrendAnalyzer`: Time-based sentiment shifts

**Output Format:**
{
"entity": "Taboola",
"total_items": 150,
"sentiment_distribution": {
"positive": 62,
"neutral": 20,
"negative": 18
},
"field_breakdown": {
"ad_quality": {"positive": 20, "negative": 80},
"revenue_potential": {"positive": 85, "negative": 15}
},
"top_themes": [
{
"theme": "Ad Intrusiveness",
"count": 45,
"sentiment": "negative",
"sample_quotes": [
"too many ads",
"disruptive experience"
]
},
{
"theme": "Good Revenue for Publishers",
"count": 38,
"sentiment": "positive",
"sample_quotes": [
"pays well",
"solid CPM"
]
}
],
"trends": {
"daily": [
{"date": "2025-11-20", "positive": 65, "negative": 35},
{"date": "2025-11-21", "positive": 60, "negative": 40}
]
}
}

---

#### 4. **UI/Visualization Layer** (`src/ui/`)

**Purpose:** Present insights in clear, interactive format

**Technology Choice:** Simple React app with Chart.js

**Key Features:**
- Sentiment distribution pie chart
- Field breakdown bar chart
- Top themes table with sample quotes
- Trend line graph (if timestamps available)
- Filters: platform, entity, date range

**Layout:**
┌─────────────────────────────────────────┐
│ Social Pulse Dashboard │
├─────────────────────────────────────────┤
│ Entity: [Taboola ▼] Platform: [All ▼]│
├──────────────┬──────────────────────────┤
│ Sentiment │ Field Breakdown │
│ Pie Chart │ Bar Chart │
├──────────────┴──────────────────────────┤
│ Top Themes Table │
│ Theme | Count | Sample Quotes │
├─────────────────────────────────────────┤
│ Trend Over Time (Line Chart) │
└─────────────────────────────────────────┘

---

## 🔑 Critical Technical Decisions

### 1. **LLM Provider**
**Choice:** Anthropic Claude 3.5 Sonnet

**Reasoning:**
- Superior structured output support
- Better at nuanced sentiment analysis
- Reliable JSON schema adherence
- Cost-effective for this scale

**Alternative:** OpenAI GPT-4 (if Claude unavailable)

### 2. **Data Sources**
**Primary:** Reddit via PRAW
- Easy API access
- Rich discussion data
- Good search capabilities

**Bonus:** LinkedIn Scraping
- Professional context for Taboola/Realize
- Higher quality discussions
- Scraping via BeautifulSoup + requests

### 3. **Sentiment Fields**
Focus on aspects relevant to ad tech industry:
- ad_quality
- user_experience  
- revenue_potential
- customer_support
- performance
- brand_reputation

### 4. **Testing Strategy**
- **Unit tests**: Sentiment parser with mocked LLM responses
- **Integration tests**: Reddit collector with real API
- **Schema validation**: Pydantic model tests

---

## 🚫 Out of Scope

**What NOT to Build:**
❌ Production deployment (Docker/K8s/CI-CD)  
❌ User authentication or multi-tenancy  
❌ Real-time streaming (batch is fine)  
❌ Advanced ML models (LLM-only)  
❌ Complex UI animations  
❌ Historical data storage (in-memory is fine)  

**Focus on:** Working prototype that demonstrates AI engineering skills

---

## 📦 Deliverables Checklist

### Code
- [ ] Reddit collector with PRAW
- [ ] LinkedIn scraper (or alternative bonus source)
- [ ] LLM sentiment analyzer with JSON schema
- [ ] Field-level analysis logic
- [ ] Aggregation engine (stats + themes)
- [ ] Simple React UI with charts
- [ ] CLI entry point (`python -m social_pulse`)

### Documentation
- [ ] README.md with setup instructions
- [ ] Design doc (≤1 page) explaining architecture
- [ ] API key setup guide (.env.example)
- [ ] agents.md (this file)
- [ ] spec.md (technical specs)

### Outputs
- [ ] `outputs/items.json` - raw collected data
- [ ] `outputs/analyzed.json` - sentiment analysis results
- [ ] `outputs/aggregates.json` - computed insights
- [ ] `outputs/report.md` or UI screenshots

### Quality
- [ ] At least 1 meaningful test
- [ ] Clean, modular code structure
- [ ] Error handling for API failures
- [ ] Comments on complex logic
- [ ] Type hints throughout

---

## 🤖 Agent-Specific Instructions

### For AI Coding Assistants (Windsurf/Claude/Copilot):

**When working on this project:**

1. **Always reference this document** before starting a new component
2. **Stick to defined output formats** - don't invent new schemas
3. **Keep scope minimal** - working prototype > perfect product
4. **Write runnable code** - avoid placeholders like `# TODO: implement`
5. **Include error handling** from the start

### Context for Each Component:

**Collectors:**
- Focus on API reliability, rate limits, data normalization
- Handle missing fields gracefully
- Log errors without crashing

**Analyzer:**
- Prioritize prompt engineering and schema validation
- Handle LLM failures (retry logic, fallbacks)
- Keep prompts concise and explicit

**Aggregator:**
- Ensure mathematical correctness
- Handle edge cases (empty data, single item)
- Validate aggregation logic with simple tests

**UI:**
- Functional > beautiful
- Clear labels and tooltips
- Mobile-responsive is nice but not required

---

## ⏱️ Estimated Timeline

**Total:** 6-8 hours (as per assignment)

**Breakdown:**
- **Day 1 (2-3 hours):** Data collection + basic LLM integration
- **Day 2 (2-3 hours):** Field-level analysis + aggregations
- **Day 3 (1-2 hours):** UI + visualization
- **Day 4 (1 hour):** Tests + documentation + polish

**Priority Order:**
1. Reddit + LLM (core functionality) ⭐
2. Aggregations + basic UI ⭐
3. Bonus source + polish
4. Tests + design doc

---

## 🎓 What This Project Demonstrates

**Technical Skills:**
✅ LLM Integration with structured outputs  
✅ API consumption and data normalization  
✅ Prompt engineering for complex tasks  
✅ Data aggregation and statistical analysis  
✅ Basic frontend development  
✅ Clean architecture and modular design  

**AI Engineering Skills:**
✅ JSON Schema design and validation  
✅ Field-level sentiment (not binary classification)  
✅ Edge case handling (sarcasm, mixed sentiment)  
✅ Reproducible LLM outputs  
✅ Agent-based architecture  

**Software Engineering:**
✅ Project structure and organization  
✅ Documentation and README  
✅ Testing strategy  
✅ Error handling and logging  

---

## 📝 Final Notes

**Remember:** This is a **take-home test**, not a production system.

**Goal:** Demonstrate competence in:
- Building real AI agents
- LLM integration best practices
- Clean, maintainable code
- Clear communication of design choices

**Not Goal:** Perfect, production-ready system with every feature

**Key Differentiator:** Field-level sentiment analysis shows deep understanding 
of NLP and business value, not just basic positive/negative classification.

---

**Good luck! 🚀**
