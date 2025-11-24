# Agent Architecture (Action-Enabled)

**Project:** social-pulse  
**Purpose:** Multi-agent reputation monitoring and engagement platform

---

## 1. Agent Architecture Overview (Implemented)

- Pipeline for brand reputation monitoring and engagement
- Agents collaborate as:
  - Collection → Analysis → Aggregation → Dashboard (UI)
- LLM (Gemini) for structured analysis and drafting; deterministic logic for orchestration, caching, and persistence

High-level flow:

Collector (Search) → Analyzer (LLM) → Aggregator (Stats) → Dashboard (UI)
                                            ↓
                                      Action Agent (Responder)
                                      ┌───────────────┐
                                      │ Reply (AI)    │
                                      │ Reply (Manual)│
                                      │ Campaigns     │
                                      │ Mark Handled  │
                                      └───────────────┘

---

## 2. Agent Definitions

### CollectorAgent
- **Purpose:** Fetch mentions from public sources and normalize them
- **Tools:** Google Search API (SerpAPI), date filtering (`days_back`), deduplication by URL
- **Input:** Keywords, platforms, time range
- **Output:** `RawItem` objects
- **Implementation:** `src/collectors/google_search.py` (current)

### AnalyzerAgent (LLM-powered)
- **Purpose:** Deep analysis of mentions using LLM
- **LLM Tasks:**
  - Sentiment analysis (positive/neutral/negative + score)
  - Rating extraction (1–5 stars if mentioned)
  - Topic extraction (pricing, support, ad_quality, etc.)
  - Category classification (complaint/review/question/praise/feature_request)
  - Key insight generation (one sentence)
  - Professional summary (10–15 words)
  - Draft response generation (if actionable)
- **Input:** `RawItem`
- **Output:** `AnalyzedItem`
- **Implementation:** `src/analyzers/sentiment.py` (current, Gemini-based)
  - Planned dedicated module: `src/analyzers/llm_analyzer.py`

### AggregatorAgent
- **Purpose:** Calculate statistics and identify trends
- **Tasks:**
  - Sentiment breakdown and averages
  - Topic frequency analysis
  - Trend detection over time
  - Identify action-required items
  - Track response metrics
- **Input:** `List[AnalyzedItem]`
- **Output:** `AggregatedStats` + filtered items
- **Implementation:** Basic in-app stats for UI (planned dedicated module: `src/aggregators/stats_aggregator.py`)

### ActionAgent (Responder)
- **Purpose:** Handle engagement via replies and campaign creation
- **Implemented via API:**
  - POST `/api/mentions/{id}/reply` (AI/manual) → persists reply, sets `response_status=sent`, invalidates cache
  - PATCH `/api/mentions/{id}/status` → updates `response_status`/`actionable`, invalidates cache
  - POST `/api/campaigns` → persists campaign; GET `/api/campaigns` lists
- **Planned sub-agents:** External posting (Reddit), campaign generation suggestions, email outreach
- **State:** `response_status`, `actionable`, `response_draft`, `assigned_to`

---

## 3. Agent Communication Flow (Implemented)

- **Pipeline mode:**
  - CollectorAgent → AnalyzerAgent → AggregatorAgent → Dashboard (UI)
- **Action mode (user-triggered):**
  - User action → ActionAgent (reply/campaign) → Update item status (`response_status`) and persist

State transitions (examples):
- `pending` → `sent` (after successful reply)
- `pending` → `in_campaign` (added to a campaign)
- `pending` → `ignored` (explicitly dismissed)

---

## 4. LLM Integration Details

- **Model:** Google Gemini 2.5 Flash (current)
- **Provider SDK:** `google-generativeai`
- **Prompting:** Concise instructions; enforce JSON; include few-shot as needed
- **Response format:** Structured JSON parsed and validated into Pydantic models
- **Error handling:** Retries with small backoff, default fallbacks for missing fields
- **Prompt templates:** Planned folder `src/prompts/` (not yet implemented)

---

### 4.1 Structured Output Validation (AnalysisResult)

- Uses a dedicated Pydantic model `AnalysisResult` in `src/analyzers/llm_analyzer.py` to validate LLM outputs.
- Fields validated include: `sentiment`, `sentiment_score (-1..1)`, `rating (1..5|None)`, `topics (List[str])`, `category`, `key_insight`, `summary`, `confidence (0..1)`, `actionable`, `response_draft`.
- Guarantees correct types/required fields before converting to domain `AnalyzedItem`.

### 4.2 Retry Logic in `_analyze_single`

- Two attempts per item:
  - Attempt 1: base prompt.
  - Attempt 2: same prompt plus explicit schema reminder to return compact JSON matching `AnalysisResult` fields.
- If JSON parsing or schema validation fails after 2 tries, a controlled exception triggers a safe fallback analysis (rule-based) to preserve pipeline continuity.

### 4.3 Provider Compatibility and Future Agent Wiring

- Current integration remains Gemini-first via `google-generativeai` for continuity and cost-effectiveness.
- The validation layer prepares the codebase for optional `pydantic-ai` Agent wiring (OpenAI or Anthropic providers) without changing the public API.
- Migration path: introduce a `pydantic-ai` Agent with `AnalysisResult` as the `result_type`, attempt Agent first, then fall back to the existing Gemini flow on failure.

## 5. Data Models (Reference)

Defined in `src/analyzers/models.py`:
- `RawItem` — normalized collector output
- `AnalyzedItem` — enhanced analysis + action fields (`sentiment_score`, `rating`, `topics`, `summary`, `response_draft`, `response_status`, `assigned_to`, etc.) with legacy compatibility
- `AggregatedStats` — totals, averages, trends, hot topics, response stats
- `Campaign` — campaign definition (theme, audience, message, channels, related items, status)

---

## 6. Future Agent Enhancements

- LinkedIn engagement agent
- Twitter/X monitoring and response
- Automated sentiment alerting
- Competitor analysis agent
- Multi-language support

Notes:
- LLMs power semantic analysis and drafting
- Rule-based logic governs routing, thresholds, status transitions, scheduling

#### 1. **Data Collection Layer** (`src/collectors/`)

**Purpose:** Fetch and normalize data from multiple sources

**Components:**
- `BaseCollector` (abstract): Common interface for all collectors
- `GoogleSearchCollector`: SerpAPI-based (implemented)
- `RedditCollector`: Uses PRAW (planned)
- `LinkedInCollector`: Scrapes public LinkedIn posts (planned)

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

**Technology Choice:** React + TypeScript (dashboard)

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
**Choice:** Google Gemini 2.5 Flash

**Reasoning:**
- Superior structured output support
- Better at nuanced sentiment analysis
- Reliable JSON schema adherence
- Cost-effective for this scale

**Alternative:** Anthropic Claude 3.5 Sonnet or OpenAI GPT-4 (if Gemini unavailable)

### 2. **Data Sources**
**Primary (current):** Google Search via SerpAPI
- Pragmatic, broad coverage of public web content
- Easy API with query control

**Planned:** Reddit via PRAW, LinkedIn scraping (public posts)
- Higher-quality discussions; additional engineering effort

### 3. **Sentiment Fields**
Focus on aspects relevant to ad tech industry:
- ad_quality
- user_experience  
- revenue_potential
- customer_support
- performance
- brand_reputation

### 4. **Testing Strategy**
- **Unit tests**: cache/db utilities, API response shapes
- **Integration tests**: FastAPI TestClient (see `tests/test_integration_e2e.py`)
- **Schema validation**: Pydantic model tests

Integration test notes:
- Uses temporary SQLite DB; seeds Taboola/Realize; exercises replies and campaigns; verifies persistence across reload.
- Uses `use_db=true` and explicit `entity` to bypass collectors/LLM and avoid cache staleness.

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
- [ ] Reddit collector with PRAW (planned)
- [ ] LinkedIn scraper (planned)
- [x] LLM sentiment analyzer (Gemini) with JSON parsing/validation
- [x] Field-level analysis logic
- [ ] Aggregation engine (stats + themes) — basic stats embedded in report step
- [ ] Simple React UI with charts (planned)
- [x] CLI entry point (`python -m src.main`)

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
