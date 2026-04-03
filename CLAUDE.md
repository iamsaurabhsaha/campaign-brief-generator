# Campaign Brief Generator Agent

## What to Build

An AI-powered Campaign Brief Generator that **guides PMMs through writing great campaign briefs** using industry best practices. Not just auto-generation — it's an interactive assistant that helps the user think through each section, catches common mistakes, and produces professional output.

---

## Research-Backed Brief Framework

Based on thorough research (HubSpot, Asana, Product Marketing Alliance, BetterBriefs, real-world examples from Apple, McDonald's, Barbie), great briefs follow a **14-section structure** and fit on **1-2 pages**.

### The 14 Essential Sections

| # | Section | What it answers | AI can help with |
|---|---------|----------------|------------------|
| 1 | **Campaign Name** | What do we call it? | Generate creative name options |
| 2 | **Background/Context** | Why now? | Pull competitive context, market triggers |
| 3 | **Objective** | What are we trying to achieve? | Auto-format as SMART goals |
| 4 | **Target Audience** | Who are we talking to? | Generate audience profiles with pain points |
| 5 | **Key Insight** | What human truth drives this? | Extract insights from data/research |
| 6 | **Positioning Statement** | How do we frame this? | Generate short (25 words) + detailed (100 words) |
| 7 | **Key Messages** | What do we say? | Generate 3-5 ranked messages |
| 8 | **Single-Minded Proposition (SMP)** | What's the ONE thing? | Generate + quality check ("and/also" test) |
| 9 | **Channel Plan** | Where do we say it? | Channel + tactic + owner + due date table |
| 10 | **Content Deliverables** | What do we produce? | List assets with specs |
| 11 | **Success Metrics/KPIs** | How do we measure? | Suggest relevant KPIs with targets |
| 12 | **Timeline** | When does each phase happen? | Generate phased timeline |
| 13 | **Budget** | How much do we spend? | Allocate across channels |
| 14 | **Approvals/RACI** | Who decides what? | Generate RACI matrix |

### Launch Tier Classification (Product Marketing Alliance)
- **Tier 0**: Company-defining (new platform) → Full brief + war room
- **Tier 1**: Major feature → Full brief
- **Tier 2**: Enhancement → Light brief
- **Tier 3**: Bug fix / minor → No brief needed

### Campaign Brief vs. Creative Brief vs. GTM Brief
- **Campaign Brief**: Strategic "what & why" (cross-functional, includes budget/KPIs)
- **Creative Brief**: Execution "how" (for creative/agency, tone/visuals)
- **GTM Brief**: Launch-specific (includes pricing, sales enablement, training)

### Top 9 Mistakes to Catch
1. Too long (>2 pages)
2. Multiple objectives (should be ONE primary)
3. Vague audience ("everyone")
4. No insight (just data, no human truth)
5. "And/also" in the SMP (not single-minded)
6. No success metrics
7. No competitive context
8. Skipping the "why now"
9. Brief changes after kickoff (need sign-off lock)

---

## Streamlit Dashboard Design

### Tab 1: "AI Brief Builder" (Main — Guided Flow)
A step-by-step wizard that guides the user through brief creation:

**Step 1 — Setup:**
- Campaign name (text input + "Suggest Names" button)
- Launch tier selector (Tier 0-3, with descriptions)
- Brief type: Campaign Brief / Creative Brief / GTM Brief

**Step 2 — Strategy:**
- Background/context (text area + "Why now?" prompt)
- Objective (text input + "Make it SMART" button that reformats)
- Target audience (text area + "Generate Audience Profile" button)

**Step 3 — Messaging:**
- Key insight (text area + "Extract Insight" button)
- Positioning statement (generate short + detailed versions)
- Key messages (generate 3-5, reorderable)
- Single-Minded Proposition (generate + "and/also" quality check with pass/fail badge)

**Step 4 — Execution:**
- Channel plan (auto-generated table with channel, tactic, owner, due date)
- Content deliverables (auto-generated list with specs)
- Timeline (phased: Awareness → Launch → Sustain → Optimize)
- Budget breakdown (pie chart if budget provided)

**Step 5 — Governance:**
- Success metrics/KPIs (auto-suggested with targets)
- RACI matrix (auto-generated based on stakeholder roles)
- Approvals needed

**Step 6 — Review & Export:**
- Full brief preview in markdown
- Brief quality score (1-10) with feedback on common mistakes
- Download as Markdown / PDF
- "Generate Creative Brief" button (auto-creates from campaign brief)

### Tab 2: "Brief Quality Checker"
- Paste any existing brief
- AI scores it against the 9 common mistakes
- Returns: quality score, issues found, improvement suggestions
- Radar chart of quality dimensions (clarity, specificity, actionability, audience focus, measurability)

### Tab 3: "Creative Concepts"
- Takes a completed brief as input
- Generates 3 creative concept options, each with:
  - Concept name and theme
  - Visual direction description
  - Headline + tagline
  - Sample copy for primary channel
  - Tone and style guidance
- Side-by-side comparison view

### Tab 4: "Brief Library"
- Saved briefs with search and filter (by type, tier, date)
- Brief cards showing name, tier, date, quality score
- Click to view/edit/duplicate
- Export all as CSV

### Tab 5: "Templates"
- Pre-built templates for common campaign types:
  - Product Launch (Tier 1)
  - Feature Update (Tier 2)
  - Competitive Response
  - Seasonal Campaign
  - Re-engagement Campaign
  - Brand Awareness
- Click template → pre-fills the Brief Builder with relevant defaults

---

## Key Files to Create

| File | Purpose |
|------|---------|
| `app.py` | Streamlit dashboard with 5 tabs |
| `brief_generator.py` | Claude API — generates each brief section |
| `quality_checker.py` | Scores briefs against best practices |
| `creative_engine.py` | Generates creative concepts from briefs |
| `brief_store.py` | JSON-based brief storage and retrieval |
| `templates.py` | Pre-built brief templates |
| `config.py` | Settings, section definitions, quality criteria |
| `requirements.txt` | Dependencies |
| `.env.example` | API key template |
| `README.md` | Documentation |

---

## Demo Mode

The app MUST work without an API key. In demo mode:
- Brief Builder shows a pre-filled example brief (for "AI-Powered Listing Generator" feature launch)
- Quality Checker shows a sample analysis
- Creative Concepts shows 3 sample concepts
- Brief Library has 3-4 sample briefs at different tiers
- All "Generate" buttons show sample outputs instead of calling Claude

---

## Project Context

This is one of 12 AI agents being built for an E-Commerce Product Marketing (AI Capabilities) role. Each agent is a standalone Streamlit app with Claude API integration.

### Tech Stack
- Python 3.9+
- Streamlit (dashboard UI)
- Anthropic Claude API (claude-sonnet-4-20250514)
- python-dotenv (for .env API key management)
- plotly + pandas (for charts/analytics)

### Conventions
- Use `anthropic` Python SDK directly
- API key from env var `ANTHROPIC_API_KEY` via `.env` file
- Include demo mode with sample data (app works without API key)
- Use dataclasses for data models
- Include logging throughout
- Type hints on all functions
- Robust JSON parsing with fallbacks for Claude responses
- Store persistent data in `data/` subdirectory as JSON files
- Color scheme: Blue #0064D2, Red #E53238, Yellow #F5AF02, Green #86B817
- Professional, clean UI with custom CSS
- All generate buttons should show a spinner while working

### Reference Implementation
See `/Users/saurabhsaha/Documents/My Applications/Competitive Intelligence Monitor Agent/` for patterns:
- app.py (Streamlit dashboard with tabs, filters, sample data, demo mode toggle)
- analyzer.py (Claude API integration pattern)
- battlecard_generator.py (structured prompt → JSON response pattern)
- chatbot.py (conversational AI pattern)

### Reference module (starting point for brief_generator.py):
`/Users/saurabhsaha/Documents/My Applications/Competitive Intelligence Monitor Agent/campaign_brief_generator.py`

### Full research document:
`/Users/saurabhsaha/Documents/My Applications/Competitive Intelligence Monitor Agent/research/campaign_brief_research.md`

### All 12 Agents in the Suite
1. Competitive Intelligence Monitor (BUILT) - ~/Documents/My Applications/Competitive Intelligence Monitor Agent/
2. GTM Launch Orchestrator - ~/Documents/My Applications/GTM Launch Orchestrator/
3. Positioning & Messaging Factory - ~/Documents/My Applications/Positioning & Messaging Factory/
4. Seller Segmentation & Persona - ~/Documents/My Applications/Seller Segmentation & Persona/
5. Insights & Research Synthesizer - ~/Documents/My Applications/Insights & Research Synthesizer/
6. **Campaign Brief Generator (THIS AGENT)** - ~/Documents/My Applications/Campaign Brief Generator/
7. Prompt Library & Management System - ~/Documents/My Applications/Prompt Library & Management System/
8. Seller Education Content Agent - ~/Documents/My Applications/Seller Education Content Agent/
9. Experimentation & A/B Test Analyst - ~/Documents/My Applications/Experimentation & A:B Test Analyst/
10. Marketing AI Governance & CoE Agent - ~/Documents/My Applications/Marketing AI Governance & CoE Agent/
